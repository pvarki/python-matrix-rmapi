# Changelog

## [1.2.1](https://github.com/pvarki/python-matrix-rmapi/compare/v1.2.0...v1.2.1) (2026-06-14)


### Bug Fixes

* add the missing -local suffix to local build action (why is it not using the common one ??) ([e4d486e](https://github.com/pvarki/python-matrix-rmapi/commit/e4d486e5ab55eb514f5230e74705e2cc361fe6e9))

## [1.2.0](https://github.com/pvarki/python-matrix-rmapi/compare/v1.1.2...v1.2.0) (2026-06-14)


### Features

* allow manual triggering of CI jobs ([b36a04f](https://github.com/pvarki/python-matrix-rmapi/commit/b36a04f3bf7237e67672e9ab62bbe8a18133890c))


### Bug Fixes

* **release-please:** do not include component in tag ([a17cd1e](https://github.com/pvarki/python-matrix-rmapi/commit/a17cd1e2416c09d49de3652625f849ac4cefe762))


### Documentation

* write changelogs for past versions ([cb90f68](https://github.com/pvarki/python-matrix-rmapi/commit/cb90f68cec7d38d5e49b0a2fcc02e89dc68f18d3))

## [1.1.2](https://github.com/pvarki/python-matrix-rmapi/releases/tag/v1.1.2) (2026-06-09)


### Features

* implement release-please for versioning and releases ([35bf3bd](https://github.com/pvarki/python-matrix-rmapi/commit/35bf3bdd243ba2da4703a913481f002a6a66564e))


### Documentation

* fix release-please changelog list ([725a561](https://github.com/pvarki/python-matrix-rmapi/commit/725a56171f9c126b1c3432239563042209960aea))
* update readme ([17604f7](https://github.com/pvarki/python-matrix-rmapi/commit/17604f74e02dc70324dd53a3585aab9c7636c214))

## 1.1.1 (2026-05-12)


### Features

* add docker image publishing to GitHub Actions ([5eb7913](https://github.com/pvarki/python-matrix-rmapi/commit/5eb7913a54ca9e13cccd9506ef4ffb444f075cd9))


### Bug Fixes

* pin urllib3 and click versions ([a7aafe7](https://github.com/pvarki/python-matrix-rmapi/commit/a7aafe7c72424e5107c8b30442b5e3ceaf759cb4))
* remove vulnerable and unneeded packages ([85b6a16](https://github.com/pvarki/python-matrix-rmapi/commit/85b6a168ed2b3f860f4a0c942cb0b6e4a052d0c8))
* use ubuntu-latest instead of arc-runner-set ([d2c414b](https://github.com/pvarki/python-matrix-rmapi/commit/d2c414bd96dade75c8955a8d2db84a16b154edf9))

## 1.1.0 (2026-05-12)


### Bug Fixes

* temporarily switch from arc-runner-set to ubuntu-latest ([f184554](https://github.com/pvarki/python-matrix-rmapi/commit/f184554933e1a3882457ae658fc402c43d96e1f0))
* update version tool in deps and add lockfile version update ([46aa1c6](https://github.com/pvarki/python-matrix-rmapi/commit/46aa1c6641434a48f4d44138a75648aaaee01dae))

## 1.0.3 (2026-04-29)


### Bug Fixes

* change delimiter to '+' instead of '-' ([2b0f867](https://github.com/pvarki/python-matrix-rmapi/commit/2b0f867e838f0ca3e05af752388b51f2d3001304))
* change poetry to install bump-my-version instead of bump2version ([c8cfd64](https://github.com/pvarki/python-matrix-rmapi/commit/c8cfd6461d43a3cfae47beb237ab26c70f7d2681))
* rename version release to build ([2daa58c](https://github.com/pvarki/python-matrix-rmapi/commit/2daa58cc26a57da983b5e8c743ab2707f5a0eb33))


### Documentation

* fix readme example ([fc507c9](https://github.com/pvarki/python-matrix-rmapi/commit/fc507c94ce48dc63731033772107e96ce1749f22))
* README versioning example changed to a more obvious effect ([bc9669c](https://github.com/pvarki/python-matrix-rmapi/commit/bc9669c7b062bc4d4424ef024f5a6ccb1d9101eb))

## 1.0.2 (2026-04-29)


### Bug Fixes

* docker build ([8cbe52e](https://github.com/pvarki/python-matrix-rmapi/commit/8cbe52e647e8c5ac41c68804f42a9dbb8cab9805))

## 1.0.1 (2026-04-12)


### Documentation

* update docs link for matrix description ([05a74b1](https://github.com/pvarki/python-matrix-rmapi/commit/05a74b1b71854f6361bc593f4bc7a8be580ebc94))

## 1.0.0 (2026-04-11)

Initial release.


### Features

* Matrix/Synapse RASENMAEHER integration API, replacing the template's fake product ([ebe952e](https://github.com/pvarki/python-matrix-rmapi/commit/ebe952e0c08e2ab1a60c8e509a39951ac11a6997))
* user CRUD against an auto-created space and rooms via a bot user, with tests ([d66cfb8](https://github.com/pvarki/python-matrix-rmapi/commit/d66cfb8885fc34d32f666296e658c2718fa934b4), [85f7a5c](https://github.com/pvarki/python-matrix-rmapi/commit/85f7a5c828c68096d0a9952a213e53be820eb3d7), [c8d5bec](https://github.com/pvarki/python-matrix-rmapi/commit/c8d5bec2fc781f10cafff8b1dc0c9ff560c9976b))
* let regular users start video calls in rooms and create rooms in autogen-space ([be1a46e](https://github.com/pvarki/python-matrix-rmapi/commit/be1a46e4bdc41f331355adb19c7bc6f2f0305146))
* call kc init scripts on container start ([f7e8a8e](https://github.com/pvarki/python-matrix-rmapi/commit/f7e8a8e56bd2a5e8fbb25dfeb84c4b7a3d547faa))
* web UI with onboarding and feature guides ([c768601](https://github.com/pvarki/python-matrix-rmapi/commit/c768601d4810b62145808af4faf7b39dd9aac389), [1dbbaef](https://github.com/pvarki/python-matrix-rmapi/commit/1dbbaefcd6330b2ce6e8899c5657ef6360bef3cc), [298f4a9](https://github.com/pvarki/python-matrix-rmapi/commit/298f4a951cdbfd643c1c77d4a1e23fa41c882ed7), [77d2f12](https://github.com/pvarki/python-matrix-rmapi/commit/77d2f1283c6bba922814151e7ebe93d79c138215))


### Bug Fixes

* add missing tox config ([3f5980e](https://github.com/pvarki/python-matrix-rmapi/commit/3f5980e6f4fd002fe81153dcf1c58e14e064bd53))
* container-init fixes ([c7bfeae](https://github.com/pvarki/python-matrix-rmapi/commit/c7bfeae6de69d03a0340d75d3cd4be11cbd933a9))
* correct package author metadata ([78e6d7b](https://github.com/pvarki/python-matrix-rmapi/commit/78e6d7baffbe40a8313251010e847864ae8bf1c3))
* fail if secret unset, better pending_promotions, less noise ([bae2fa5](https://github.com/pvarki/python-matrix-rmapi/commit/bae2fa57caf531df22874846650ea3fd034b5de5))
* healthcheck error ([d198af2](https://github.com/pvarki/python-matrix-rmapi/commit/d198af204b41e5d49e062f2546faa36a141877ca))
* onboarding loading ([2b2413a](https://github.com/pvarki/python-matrix-rmapi/commit/2b2413aa7074df1f1a5de020e81d6b37e9bd518a))
* prevent race condition in init script ([af656c6](https://github.com/pvarki/python-matrix-rmapi/commit/af656c62a120883ea0cbe863e01701351c6acce0))
* remove https from mtls url ([13cc26a](https://github.com/pvarki/python-matrix-rmapi/commit/13cc26a4e760a0a656f7af8b2b58a2af7463362b))
* use correct action versions, drop old custom action ([af71db0](https://github.com/pvarki/python-matrix-rmapi/commit/af71db014954d74f15585e93a8b8bed62e6aa1a1))
