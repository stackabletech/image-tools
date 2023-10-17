# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

# [0.0.4] - 2023-10-17

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
