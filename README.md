# Zotero 10 Local Plugin

[中文说明](README.zh-CN.md) · MIT · Independent community fork

A Codex/Agent Plugin for Zotero Desktop: library search, existing-note updates,
stored attachments, collections, tags, annotations, saved searches, full text,
citations and imports. It extends OpenAI's Zotero 0.1.2 plugin through Zotero 10's
official local API. It is installed in the **agent host**, not as a Zotero XPI.

## Requirements

- Python 3.10+ (standard library only), a local Zotero Desktop installation, and
  an agent host that supports local plugins or Agent Skills.
- Zotero 10+ for official local API writes. Older clients support a smaller
  read/Connector feature set. Check the actual running client with `status`.
- Enable Zotero's local API in its settings when required. The helper reports
  connectivity; installing this repository does not modify the library.

## Install

Download and extract a versioned **source ZIP** from [Releases](https://github.com/YkxbGcl2001/zotero-10-local-plugin/releases),
or clone this repository. In a Codex CLI with plugin marketplace support:

```sh
codex plugin marketplace add YkxbGcl2001/zotero-10-local-plugin
codex plugin add zotero-10@research-local
```

`research-local` is the catalog identifier. If you already use a different catalog
with that name, use the standalone Skill alternative below to avoid a collision.
For hosts that import a plugin directory, select `plugins/zotero-10` or extract
the release's **plugin ZIP**. Start a new chat after installation; host discovery
and marketplace support depend on your installed host version.

Alternative: install the same packaged instructions and CLI as a standalone Skill:

```sh
python3 scripts/install_skill.py
```

It copies the complete Skill to `~/.agents/skills/zotero-10` without overwriting an
existing installation. Use `--dest /path/to/skills` for a host using another Skills
directory (including legacy `~/.codex/skills`). No global configuration is changed.

## First use

Select Zotero 10 in the host and ask it to search the library. To diagnose without
an agent, run from the source repository:

```sh
python3 plugins/zotero-10/skills/zotero-10/scripts/zotero10.py status --json
python3 plugins/zotero-10/skills/zotero-10/scripts/zotero10.py --help
```

Reads need no API key. Writes require Zotero's own Allow/Always Allow consent
dialog; the agent cannot approve it on your behalf. Multi-request attachment
uploads need persistent permission. Tokens are stored outside the repository in
`~/.codex/zotero10/authorizations` with restricted permissions; do not publish them.
Write commands require `--yes` to execute work the user has authorized. Update
conflicts are reported rather than bypassed. Source PDFs are not deleted.

## Validation and limits

```sh
python3 -B -m unittest discover -s plugins/zotero-10/tests -v
python3 -B scripts/build.py
```

Thirty tests use a mocked HTTP transport and temporary files. They verify command
behavior and failure handling; they do not prove a write against your running
library. The release does not perform live writes or restart Zotero. Desktop-only
features, third-party Zotero extensions and Word dynamic citations have separate
boundaries: see [capabilities](plugins/zotero-10/skills/zotero-10/references/features-and-compatibility.md).
macOS local use has been checked; Windows/Linux profile discovery is implemented
but has not been tested on physical Windows/Linux machines for this release.

The source ZIP includes code, tests, licenses, documentation, the catalog and
build/install scripts. The plugin ZIP includes both manifests and all runtime
Skill references, scripts and icons. Neither includes credentials or library data.
See [third-party attribution](THIRD_PARTY_NOTICES.md), [MIT license](LICENSE), and
[official plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).
