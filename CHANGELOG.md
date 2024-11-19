# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## Added

- Add `--target-containerfile` argument to override the default `Dockerfile` value ([#44]).
- Add `--list-products` argument to get a machine-readable (JSON) output of all products and their versions ([#45]).

[#44]: https://github.com/stackabletech/image-tools/pull/44
[#45]: https://github.com/stackabletech/image-tools/pull/45

## 0.0.13 - 2024-09-06

### Added

- `conf.py` now can contain a `args` dict, which contains arguments available to all products, they
  can be overridden by product specific or CLI arguments ([#41]).

### Fixed

- `--build-arg` was not case-insensitive as claimed in the docs, this has been  fixed ([#41]).

[#41]: https://github.com/stackabletech/image-tools/pull/41

## [0.0.12] - 2024-07-08

### Added

- New `bake` command line argument `--build-arg` to override conf.py build arguments ([#38]).

### Fixed

- check-container: fix regression introduced by 0.0.9. Add dummy cache property ([#39]).

[#38]: https://github.com/stackabletech/image-tools/pull/38
[#39]: https://github.com/stackabletech/image-tools/pull/39

## [0.0.11]

### Added

- Automatically create labels and annotations recording the git revision and build time ([#34]).

[#34]: https://github.com/stackabletech/image-tools/pull/34

## [0.0.10] - 2024-07-03

### Fixed

- Add architecture identifier to the build cache backend ref name ([#31]).
- Backwards compat: don't assume conf.cache exists ([#32]).

[#31]: https://github.com/stackabletech/image-tools/pull/31
[#32]: https://github.com/stackabletech/image-tools/pull/32

## [0.0.9] - 2024-07-02

### Added

- New command line arg to `bake`: `--cache`. Requires cache backend configuration in
  `conf.py` ([#29]).

[#29]: https://github.com/stackabletech/image-tools/pull/29

## [0.0.8] - 2024-07-02

### Added

- New command line arg to `bake`: `--version`. Also switch to relative imports ([#17]).
- Raise lint dependency versions ([#17]).
- Drop support for python 3.10 and add explicit support for 3.12 ([#17]).

### Fixed

- Use cwd in module path so imports in `conf.py` work ([#27]).

[#17]: https://github.com/stackabletech/image-tools/pull/17
[#27]: https://github.com/stackabletech/image-tools/pull/27

## [0.0.7] - 2024-05-02

### Fixed

- Invalid 'buildx bake' configuration file generated due to architecture not being a list
  anymore ([#13]).

[#13]: https://github.com/stackabletech/image-tools/pull/13

## [0.0.6] - 2024-04-24

### Changed

- Add platform argument for preflight checks ([#12]).

[#12]: https://github.com/stackabletech/image-tools/pull/12

## [0.0.5] - 2023-10-19

### Changed

- Relax schema for image tags ([#7]).

[#7]: https://github.com/stackabletech/image-tools/pull/7

## [0.0.4] - 2023-10-17

### Added

- New `bake` argument (`--export-tags-file`) to write target tags to text file ([#4]).

### Changed

- Changed `conf` schema to drop support for versions as strings. Only dicts are supported ([#4]).

[#4]: https://github.com/stackabletech/image-tools/pull/4

## [0.0.3] - 2023-10-16

### Added

- Allow `bake` product names to accept a version as suffix separated by "=" ([#2]).
- New `bake` command line options `--shard-index` and `--shard-count` ([#2]).

### Changed

- Make stackable image version (`-i`) for `bake` optional and default to `0.0.0-dev` ([#2]).

[#2]: https://github.com/stackabletech/image-tools/pull/2
