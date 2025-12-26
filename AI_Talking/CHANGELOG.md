# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.7] - 2025-12-26

### Added
- Added "修改" (Edit) button to discussion history bubbles
- Added message editing functionality with auto-save feature

### Changed
- Updated button order in discussion history: Edit, Copy, Delete
- Optimized all internationalization language packs for accuracy and brevity
- Updated version number from 0.3.6 to 0.3.7
- Updated configuration files (__init__.py, about_tab.py, AI_Talking_Setup.iss)
- Created v0.3.7 RELEASE_NOTES.md and latest.json files

### Fixed
- Fixed button functionality in discussion and debate history
- Ensured proper event binding for dynamically added elements
- Fixed CSS selector issues for button targeting

## [0.3.6] - 2025-12-25

### Added
- Added support for Korean, German, Spanish, French, Arabic, and Russian languages
- Added missing translation keys to all language files

### Changed
- Updated version number from 0.3.4 to 0.3.6
- Updated AI_Talking.spec file with all necessary hidden import modules
- Updated pathex and datas configurations in spec file to ensure proper packaging of resources

### Fixed
- Fixed discussion history button functionality by changing from positional selectors to class selectors (edit-btn, copy-btn, delete-btn)
- Fixed language switching crash
- Fixed state messages not updating with language changes
- Fixed JSON syntax errors in language files
- Fixed proper packaging of i8n directory and resources directory
- Ensured all language files use correct language content

## [0.3.5] - 2025-12-24

### Changed
- Updated version number from 0.3.4 to 0.3.5

## [0.3.4] - 2025-12-23

### Initial Release
- First public release of AI_Talking application
- Basic chat, discussion, and debate functionality
- Support for multiple AI models
- Internationalization support for English, Chinese (Simplified), Chinese (Traditional), and Japanese
