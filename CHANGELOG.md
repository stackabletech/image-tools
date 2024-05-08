# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- New command line arg to `bake`: `--version`. Also switch to relative imports. ([#17])
- Raise lint dependency versions ([#17])
- Drop support for python 3.10 and add explicit support for 3.12 ([#17])

[#17]: https://github.com/stackabletech/image-tools/pull/17


## 0.0.7

### Fixed

- Invalid 'buildx bake' configuration file generated due to architecture not being a list anymore. ([#13])

[#13]: https://github.com/stackabletech/image-tools/pull/13

## [0.0.6] - 2024-04-24

### Changed

- Add platform argument for preflight checks ([#12])

[#12]: https://github.com/stackabletech/image-tools/pull/12

## [0.0.5] - 2023-10-19

### Changed

- Relax schema for image tags ([#7])

[#7]: https://github.com/stackabletech/image-tools/pull/7

## [0.0.4] - 2023-10-17

### Added

- New `bake` argument (`--export-tags-file`) to write target tags to text file ([#4])

### Changed

- Changed `conf` schema to drop support for versions as strings. Only dicts are supported ([#4])

[#4]: https://github.com/stackabletech/image-tools/pull/4

## [0.0.3] - 2023-10-16

### Added

- Allow `bake` product names to accept a version as suffix separated by "=" ([#2])
- New `bake` command line options `--shard-index` and `--shard-count` ([#2])

### Changed

- Make stackable image version (`-i`) for `bake` optional and default to `0.0.0-dev` ([#2])

[#2]: https://github.com/stackabletech/image-tools/pull/2
