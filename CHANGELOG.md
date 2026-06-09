# Changelog

## [1.1.2](https://github.com/pvarki/python-matrix-rmapi/compare/matrixrmapi-v1.1.1...matrixrmapi-v1.1.2) (2026-06-09)


### Features

* add docker image publishing to GitHub Actions ([5eb7913](https://github.com/pvarki/python-matrix-rmapi/commit/5eb7913a54ca9e13cccd9506ef4ffb444f075cd9))
* add guide content to ui minus images, and fix linting issues with tests ([298f4a9](https://github.com/pvarki/python-matrix-rmapi/commit/298f4a951cdbfd643c1c77d4a1e23fa41c882ed7))
* add initial ui ([c768601](https://github.com/pvarki/python-matrix-rmapi/commit/c768601d4810b62145808af4faf7b39dd9aac389))
* added homeserver url ([5167bb3](https://github.com/pvarki/python-matrix-rmapi/commit/5167bb390f8f94cded609af8d8d5ea11371a1029))
* call kc init scripts ([f7e8a8e](https://github.com/pvarki/python-matrix-rmapi/commit/f7e8a8e56bd2a5e8fbb25dfeb84c4b7a3d547faa))
* complete user crud to autocreated space and rooms via a bot user ([85f7a5c](https://github.com/pvarki/python-matrix-rmapi/commit/85f7a5c828c68096d0a9952a213e53be820eb3d7))
* correct port number ([3194864](https://github.com/pvarki/python-matrix-rmapi/commit/3194864ca4f2f31821e4b32e0dc02c6c35707dc7))
* first commit ([f71d452](https://github.com/pvarki/python-matrix-rmapi/commit/f71d4528c04057200dd71de0a80bf3c87a501a11))
* images & texts to UI featureguides, and add dev img:min script ([77d2f12](https://github.com/pvarki/python-matrix-rmapi/commit/77d2f1283c6bba922814151e7ebe93d79c138215))
* let regular users start video calls in rooms and create rooms in autogen-space ([be1a46e](https://github.com/pvarki/python-matrix-rmapi/commit/be1a46e4bdc41f331355adb19c7bc6f2f0305146))
* minimally implement user crud, auto-create & join a space & rooms ([d66cfb8](https://github.com/pvarki/python-matrix-rmapi/commit/d66cfb8885fc34d32f666296e658c2718fa934b4))
* onboarding ([1dbbaef](https://github.com/pvarki/python-matrix-rmapi/commit/1dbbaefcd6330b2ce6e8899c5657ef6360bef3cc))
* replace fake with matrix ([ebe952e](https://github.com/pvarki/python-matrix-rmapi/commit/ebe952e0c08e2ab1a60c8e509a39951ac11a6997))
* tests for user crud ([c8d5bec](https://github.com/pvarki/python-matrix-rmapi/commit/c8d5bec2fc781f10cafff8b1dc0c9ff560c9976b))
* use our arc-runner-set in build testing, for speed ([74ec40c](https://github.com/pvarki/python-matrix-rmapi/commit/74ec40c7364797941d2d113466d5305ef32b8e20))
* use our arc-runner-set in build testing, for speed ([c8905ca](https://github.com/pvarki/python-matrix-rmapi/commit/c8905ca94a0535b48cc583cc5aee7124c4c02fe8))


### Bug Fixes

* add missing tox config ([3f5980e](https://github.com/pvarki/python-matrix-rmapi/commit/3f5980e6f4fd002fe81153dcf1c58e14e064bd53))
* change delimiter to '+' instead of '-' ([2b0f867](https://github.com/pvarki/python-matrix-rmapi/commit/2b0f867e838f0ca3e05af752388b51f2d3001304))
* change poetry to install bump-my-version instead of bump2version ([c8cfd64](https://github.com/pvarki/python-matrix-rmapi/commit/c8cfd6461d43a3cfae47beb237ab26c70f7d2681))
* container-init fixes ([c7bfeae](https://github.com/pvarki/python-matrix-rmapi/commit/c7bfeae6de69d03a0340d75d3cd4be11cbd933a9))
* correct integration name ([a667932](https://github.com/pvarki/python-matrix-rmapi/commit/a6679329dcce17fb054626ba6fcafdcab0e8b652))
* docker build ([8cbe52e](https://github.com/pvarki/python-matrix-rmapi/commit/8cbe52e647e8c5ac41c68804f42a9dbb8cab9805))
* fail if secret unset, better pending_promotions, less noise ([bae2fa5](https://github.com/pvarki/python-matrix-rmapi/commit/bae2fa57caf531df22874846650ea3fd034b5de5))
* healthcheck error ([d198af2](https://github.com/pvarki/python-matrix-rmapi/commit/d198af204b41e5d49e062f2546faa36a141877ca))
* I am not the actual author ([78e6d7b](https://github.com/pvarki/python-matrix-rmapi/commit/78e6d7baffbe40a8313251010e847864ae8bf1c3))
* miscellaneous issues with names etc. ([b66326a](https://github.com/pvarki/python-matrix-rmapi/commit/b66326ad15caa9490a1d5ac099fbd5a31e337e19))
* onboarding loading ([2b2413a](https://github.com/pvarki/python-matrix-rmapi/commit/2b2413aa7074df1f1a5de020e81d6b37e9bd518a))
* pin urllib3 and click versions ([a7aafe7](https://github.com/pvarki/python-matrix-rmapi/commit/a7aafe7c72424e5107c8b30442b5e3ceaf759cb4))
* prevent race condition in init script ([af656c6](https://github.com/pvarki/python-matrix-rmapi/commit/af656c62a120883ea0cbe863e01701351c6acce0))
* remove fake product mentions ([bda5748](https://github.com/pvarki/python-matrix-rmapi/commit/bda5748bf7daa10aa49d2b216e556492ae765aa4))
* remove https from mtls url ([13cc26a](https://github.com/pvarki/python-matrix-rmapi/commit/13cc26a4e760a0a656f7af8b2b58a2af7463362b))
* remove vulnerable and unneeded packages ([85b6a16](https://github.com/pvarki/python-matrix-rmapi/commit/85b6a168ed2b3f860f4a0c942cb0b6e4a052d0c8))
* rename version release to build ([2daa58c](https://github.com/pvarki/python-matrix-rmapi/commit/2daa58cc26a57da983b5e8c743ab2707f5a0eb33))
* temporarily switch from arc-runner-set to ubuntu-latest ([f184554](https://github.com/pvarki/python-matrix-rmapi/commit/f184554933e1a3882457ae658fc402c43d96e1f0))
* update version tool in deps and add lockfile version update ([46aa1c6](https://github.com/pvarki/python-matrix-rmapi/commit/46aa1c6641434a48f4d44138a75648aaaee01dae))
* use correct action versions and drop the old useless custom action. Ensure version number is bumped ([af71db0](https://github.com/pvarki/python-matrix-rmapi/commit/af71db014954d74f15585e93a8b8bed62e6aa1a1))
* use ubuntu-latest instead of arc-runner-set ([d2c414b](https://github.com/pvarki/python-matrix-rmapi/commit/d2c414bd96dade75c8955a8d2db84a16b154edf9))
* versioning ([014dc5d](https://github.com/pvarki/python-matrix-rmapi/commit/014dc5d5cff71d0519adefb218f0bfd4417d69a6))


### Documentation

* fix readme example ([fc507c9](https://github.com/pvarki/python-matrix-rmapi/commit/fc507c94ce48dc63731033772107e96ce1749f22))
* fix release-please changelog list ([725a561](https://github.com/pvarki/python-matrix-rmapi/commit/725a56171f9c126b1c3432239563042209960aea))
* README versioning example changed to a more obvious effect ([bc9669c](https://github.com/pvarki/python-matrix-rmapi/commit/bc9669c7b062bc4d4424ef024f5a6ccb1d9101eb))
* update readme ([17604f7](https://github.com/pvarki/python-matrix-rmapi/commit/17604f74e02dc70324dd53a3585aab9c7636c214))
