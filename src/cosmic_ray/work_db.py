"""Implementation of the WorkDB."""

import contextlib
from pathlib import Path

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm.session import sessionmaker

from .work_item import ResolvedMutationSpec, TestOutcome, WorkResult, WorkerOutcome, WorkItem


class WorkDB:
    """WorkDB is the database that keeps track of mutation testing work progress.

    Essentially, there's a row in the DB for each mutation that needs to be
    executed in some run. These initially start off with no results, and
    results are added as they're completed.
    """

    class Mode(Enum):
        "Modes in which a WorkDB may be opened."

        # Open existing files, creating if necessary
        create = 1

        # Open only existing files, failing if it doesn't exist
        open = 2

    def __init__(self, path, mode):
        """Open a DB in file `path` in mode `mode`.

        Args:
          path: The path to the DB file.

        Raises:
          FileNotFoundError: If `mode` is `Mode.open` and `path` does not
            exist.
        """
        self._path = path
        if mode == WorkDB.Mode.open and (not Path(path).exists()):
            raise FileNotFoundError("File does not exist: {}".format(path))

        self._engine = create_engine("sqlite:///{}".format(path))

        def enable_foreign_keys(dbapi_con, _con_rec):
            dbapi_con.execute("pragma foreign_keys=ON")

        event.listen(self._engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self._engine)
        self._session_maker = sessionmaker(self._engine)

    def close(self):
        """Close the database."""
        # TODO: We don't really need this any more. Should we just remove it? Similarly, is there any need
        # for use_db()? It seems possible that we'll eventually move back to needing an explicit close()
        # call, so I'm a bit hesitant to remove this.

    def name(self):
        """A name for this database.

        Derived from the constructor arguments.
        """
        return str(self._path)

    @property
    def work_items(self):
        """An iterable of all of WorkItems in the db.

        This includes both WorkItems with and without results.
        """
        with self._session_maker.begin() as session:
            return tuple(_work_item_from_storage(work_item) for work_item in session.query(WorkItemStorage).all())

    @property
    def num_work_items(self):
        """The number of work items."""
        with self._session_maker.begin() as session:
            return session.query(WorkItemStorage).count()

    def add_work_item(self, work_item):
        """Add a :class:`WorkItem`.

        Args:
          work_item: A ``WorkItem``.
        """
        self.add_work_items((work_item,))

    def add_work_items(self, work_items):
        """Add multiple WorkItems.

        Args:
          work_items: an iterable of WorkItem.
        """
        storage = (_work_item_to_storage(work_item) for work_item in work_items)

        with self._session_maker.begin() as session:
            session.add_all(storage)

    def clear(self):
        """Clear all work items from the session.

        This removes any associated results as well.
        """
        with self._session_maker.begin() as session:
            session.query(WorkResultStorage).delete()
            session.query(MutationSpecStorage).delete()
            session.query(WorkItemStorage).delete()

    @property
    def results(self):
        "An iterable of all ``(job-id, WorkResult)``\\s."
        with self._session_maker.begin() as session:
            for result in session.query(WorkResultStorage).all():
                yield result.job_id, _work_result_from_storage(result)

    @property
    def num_results(self):
        """The number of results."""
        with self._session_maker.begin() as session:
            return session.query(WorkResultStorage).count()

    def set_result(self, job_id, result):
        """Set the result for a job.

        This will overwrite any existing results for the job.

        Args:
          job_id: The ID of the WorkItem to set the result for.
          result: A WorkResult indicating the result of the job.

        Raises:
           KeyError: If there is no work-item with a matching job-id.
        """
        try:
            with self._session_maker.begin() as session:
                storage = _work_result_to_storage(result, job_id)
                session.merge(storage)
        except IntegrityError:
            raise KeyError("Unable to add results for job-id {}. No matching WorkItem.".format(job_id))

    @property
    def pending_work_items(self):
        "Iterable of all pending work items. In random order."
        with self._session_maker.begin() as session:
            completed_job_ids = session.query(WorkResultStorage.job_id)
            pending = session.query(WorkItemStorage).where(~WorkItemStorage.job_id.in_(completed_job_ids))
            return tuple(_work_item_from_storage(work_item) for work_item in pending)

    @property
    def completed_work_items(self):
        "Iterable of ``(work-item, result)``\\s for all completed items."
        with self._session_maker.begin() as session:
            results = session.query(WorkItemStorage, WorkResultStorage).where(
                WorkItemStorage.job_id == WorkResultStorage.job_id
            )
            return tuple(
                (_work_item_from_storage(work_item), _work_result_from_storage(result)) for work_item, result in results
            )


@contextlib.contextmanager
def use_db(path, mode=WorkDB.Mode.create):
    """
    Open a DB in file `path` in mode `mode` as a context manager.

    On exiting the context the DB will be automatically closed.

    Args:
      path: The path to the DB file.

    Raises:
      FileNotFoundError: If `mode` is `Mode.open` and `path` does not
        exist.
    """
    database = WorkDB(path, mode)
    try:
        yield database

    finally:
        database.close()


Base = declarative_base()


class WorkItemStorage(Base):
    "Database model for WorkItem."
    __tablename__ = "work_items"

    job_id = Column(String, primary_key=True)
    mutations = relationship("MutationSpecStorage", back_populates="work_item")


class MutationSpecStorage(Base):
    "Database model for MutationSpecs"
    __tablename__ = "mutation_specs"
    module_path = Column(String)
    operator_name = Column(String)
    occurrence = Column(Integer)
    start_pos_row = Column(Integer)
    start_pos_col = Column(Integer)
    end_pos_row = Column(Integer)
    end_pos_col = Column(Integer)
    job_id = Column(String, ForeignKey("work_items.job_id"), primary_key=True)
    work_item = relationship("WorkItemStorage", back_populates="mutations")


class WorkResultStorage(Base):
    "Database model for WorkResult."
    __tablename__ = "work_results"

    worker_outcome = Column(Enum(WorkerOutcome))
    output = Column(Text, nullable=True)
    test_outcome = Column(Enum(TestOutcome), nullable=True)
    diff = Column(Text, nullable=True)
    job_id = Column(String, ForeignKey("work_items.job_id"), primary_key=True)


def _mutation_spec_from_storage(mutation_spec: MutationSpecStorage):
    return ResolvedMutationSpec(
        module_path=Path(mutation_spec.module_path),
        operator_name=mutation_spec.operator_name,
        occurrence=mutation_spec.occurrence,
        start_pos=(mutation_spec.start_pos_row, mutation_spec.start_pos_col),
        end_pos=(mutation_spec.end_pos_row, mutation_spec.end_pos_col),
    )


def _mutation_spec_to_storage(mutation_spec: ResolvedMutationSpec, job_id: str):
    return MutationSpecStorage(
        job_id=job_id,
        module_path=str(mutation_spec.module_path),
        operator_name=mutation_spec.operator_name,
        occurrence=mutation_spec.occurrence,
        start_pos_row=mutation_spec.start_pos[0],
        start_pos_col=mutation_spec.start_pos[1],
        end_pos_row=mutation_spec.end_pos[0],
        end_pos_col=mutation_spec.end_pos[1],
    )


def _work_item_from_storage(work_item: WorkItemStorage):
    return WorkItem(
        mutations=tuple(_mutation_spec_from_storage(s) for s in work_item.mutations),
        job_id=work_item.job_id,
    )


def _work_item_to_storage(work_item: WorkItem):
    return WorkItemStorage(
        job_id=work_item.job_id,
        mutations=[_mutation_spec_to_storage(mutation, work_item.job_id) for mutation in work_item.mutations],
    )


def _work_result_to_storage(result: WorkResult, job_id):
    return WorkResultStorage(
        worker_outcome=result.worker_outcome,
        output=result.output,
        test_outcome=result.test_outcome,
        diff=result.diff,
        job_id=job_id,
    )


def _work_result_from_storage(result: WorkResultStorage):
    return WorkResult(
        worker_outcome=result.worker_outcome,
        output=result.output,
        test_outcome=result.test_outcome,
        diff=result.diff,
    )
