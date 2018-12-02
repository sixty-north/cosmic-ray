((nil . (;(projectile-project-test-cmd . "pytest python/test")
            (eval .(unless (and (boundp 'pyvenv-virtual-env-name) (equal pyvenv-virtual-env-name "cosmic-ray"))
                       (pyvenv-workon "cosmic-ray"))))))
