"Implementation of the 'init' command."

import ast
import enum
import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

import cosmic_ray.plugins
from cosmic_ray.ast import ast_nodes, get_ast_from_path
from cosmic_ray.util import read_python_source
from cosmic_ray.work_db import WorkDB
from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome

log = logging.getLogger()


class AnnotationContext(str, enum.Enum):
    ANNASSIGN = "annassign"
    PARAM = "param"
    RETURN = "return"
    TYPE_ALIAS = "type_alias"


@dataclass(frozen=True)
class AnnotationSpan:
    start_pos: tuple[int, int]
    end_pos: tuple[int, int]
    context: AnnotationContext


def _node_position(node):
    lineno = getattr(node, "lineno", None)
    col_offset = getattr(node, "col_offset", None)
    end_lineno = getattr(node, "end_lineno", None)
    end_col_offset = getattr(node, "end_col_offset", None)
    if None in (lineno, col_offset, end_lineno, end_col_offset):
        return None
    return (lineno, col_offset), (end_lineno, end_col_offset)


def _annotation_spans(source):
    tree = ast.parse(source, type_comments=True)
    spans = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            pos = _node_position(node.annotation)
            if pos:
                spans.append(AnnotationSpan(*pos, AnnotationContext.ANNASSIGN))

        if isinstance(node, ast.arg) and node.annotation is not None:
            pos = _node_position(node.annotation)
            if pos:
                spans.append(AnnotationSpan(*pos, AnnotationContext.PARAM))

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
            pos = _node_position(node.returns)
            if pos:
                spans.append(AnnotationSpan(*pos, AnnotationContext.RETURN))

        type_alias_cls = getattr(ast, "TypeAlias", None)
        if type_alias_cls and isinstance(node, type_alias_cls):
            pos = _node_position(node.value)
            if pos:
                spans.append(AnnotationSpan(*pos, AnnotationContext.TYPE_ALIAS))

    return tuple(spans)


def _position_inside_range(start_pos, end_pos, range_start, range_end):
    return start_pos >= range_start and end_pos <= range_end


def _annotation_contexts_to_filter(annotation_filter_cfg):
    allowed_context_names = set(annotation_filter_cfg.get("allow-contexts", ()))
    known_contexts_by_name = {context.value: context for context in AnnotationContext}
    unknown_contexts = allowed_context_names - set(known_contexts_by_name)
    if unknown_contexts:
        unknown_list = ", ".join(sorted(unknown_contexts))
        valid_list = ", ".join(sorted(known_contexts_by_name))
        raise ValueError(f"Unknown annotation contexts in allow-contexts: {unknown_list}. Valid contexts: {valid_list}")
    allowed_contexts = {known_contexts_by_name[name] for name in allowed_context_names}
    return set(AnnotationContext) - allowed_contexts


def _operators(operator_cfgs):
    """Find all Operator instances that should be used for the session.

    Args:
        operator_cfgs (Mapping[str, Iterable[Mapping[str, Any]]]): Mapping
            of operator names to arguments sets for that operator. Each
            argument set for an operator will result in an instance of the
            operator.

    Yields:
        operators: tuples of (operator name, argument dict, operator instance).

    Raises:
        TypeError: The arguments supplied to an operator are invalid.
    """
    # TODO: Can/should we check for operator arguments which don't correspond to
    # *any* known operator?

    for operator_name in cosmic_ray.plugins.operator_names():
        operator_class = cosmic_ray.plugins.get_operator(operator_name)
        if not operator_class.arguments():
            if operator_name in operator_cfgs:
                raise TypeError(f"Arguments provided for operator {operator_name} which accepts no arguments")

            yield operator_name, {}, operator_class()
        else:
            for operator_args in operator_cfgs.get(operator_name, ()):
                yield operator_name, operator_args, operator_class(**operator_args)


def _all_work_items(module_paths, operator_cfgs) -> Iterable[WorkItem]:
    """Iterable of all WorkItems for the given inputs.

    Raises:
        TypeError: If an operator is provided with a parameterization it can't use.
    """

    for module_path in module_paths:
        module_ast = get_ast_from_path(module_path)

        for operator_name, operator_args, operator in _operators(operator_cfgs):
            positions = (
                (start_pos, end_pos)
                for node in ast_nodes(module_ast)
                for start_pos, end_pos in operator.mutation_positions(node)
            )

            for occurrence, (start_pos, end_pos) in enumerate(positions):
                mutation = MutationSpec(
                    module_path=str(module_path),
                    operator_name=operator_name,
                    operator_args=operator_args,
                    occurrence=occurrence,
                    start_pos=start_pos,
                    end_pos=end_pos,
                )
                yield WorkItem.single(job_id=uuid.uuid4().hex, mutation=mutation)


def _skip_annotation_work_items(work_db: WorkDB, annotation_filter_cfg):
    contexts_to_filter = _annotation_contexts_to_filter(annotation_filter_cfg)
    if not contexts_to_filter:
        return

    @lru_cache
    def spans_for_module(module_path):
        source = read_python_source(module_path)
        return tuple(span for span in _annotation_spans(source) if span.context in contexts_to_filter)

    for item in work_db.pending_work_items:
        if any(
            any(
                _position_inside_range(mutation.start_pos, mutation.end_pos, span.start_pos, span.end_pos)
                for span in spans_for_module(mutation.module_path)
            )
            for mutation in item.mutations
        ):
            work_db.set_result(
                item.job_id,
                WorkResult(
                    worker_outcome=WorkerOutcome.SKIPPED,
                    output="Filtered annotation mutation",
                ),
            )


def init(module_paths, work_db: WorkDB, operator_cfgs, annotation_filter_cfg=None):
    """Clear and initialize a work-db with work items.

    Any existing data in the work-db will be cleared and replaced with entirely
    new work orders. In particular, this means that any results in the db are
    removed.

    Args:
      module_paths: iterable of pathlib.Paths of modules to mutate.
      work_db: A `WorkDB` instance into which the work orders will be saved.
      operator_cfgs: A dict mapping operator names to parameterization dicts.
      annotation_filter_cfg: Optional mapping for filtering annotation mutations.
        Uses the key ``allow-contexts`` with a list of contexts to allow:
        ``annassign``, ``param``, ``return``, ``type_alias``. Any annotation
        context not listed is marked ``SKIPPED`` during init. If omitted, all
        annotation contexts are filtered.

    Raises:
        TypeError: Arguments provided for an operator are invalid.
    """
    # By default each operator will be parameterized with an empty dict.
    if annotation_filter_cfg is None:
        annotation_filter_cfg = {}

    work_db.clear()
    work_db.add_work_items(_all_work_items(module_paths, operator_cfgs))
    _skip_annotation_work_items(work_db, annotation_filter_cfg)
