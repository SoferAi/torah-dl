# `torah-dl`

SoferAI&#x27;s Torah Downloader

**Usage**:

```console
$ torah-dl [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--version`
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `extract`: Extract information from a given URL
* `download`: Download a file from a URL and show progress.
* `list`: List all available extractors.

## `torah-dl extract`

Extract information from a given URL

**Usage**:

```console
$ torah-dl extract [OPTIONS] URL
```

**Arguments**:

* `URL`: [required]

**Options**:

* `--url-only`: Only output the download URL
* `--help`: Show this message and exit.

## `torah-dl download`

Download a file from a URL and show progress.

**Usage**:

```console
$ torah-dl download [OPTIONS] URL [OUTPUT_PATH]
```

**Arguments**:

* `URL`: URL to download  [required]
* `[OUTPUT_PATH]`: Path to save the downloaded file  [default: audio]

**Options**:

* `--help`: Show this message and exit.

## `torah-dl list`

List all available extractors.

**Usage**:

```console
$ torah-dl list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
