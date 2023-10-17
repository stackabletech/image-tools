# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- New `bake` argument (`--export-tags-file`) to write target tags to text file ([#3])

[#3]: https://github.com/stackabletech/image-tools/pull/3

## [0.0.3] - 2023-10-16

### Added

- Allow `bake` product names to accept a version as suffix separated by "=" ([#2])
- New `bake` command line options `--shard-index` and `--shard-count` ([#2])

### Changed

- Make stackable image version (`-i`) for `bake` optional and default to `0.0.0-dev` ([#2])

[#2]: https://github.com/stackabletech/image-tools/pull/2
