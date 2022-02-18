# Label-Wizard

Downloads YouTube videos to annotate with bounding boxes for object detection.

![alt text](https://github.com/joshwinebrener/label-wizard/blob/master/screenshot.png?raw=true)

- [Label-Wizard](#label-wizard)
  - [Intalling requirements](#intalling-requirements)
  - [Running](#running)
  - [Building](#building)
  - [Known Issues](#known-issues)
    - [PyTube Error `urllib.error.HTTPError: HTTP Error 410: Gone`](#pytube-error-urlliberrorhttperror-http-error-410-gone)
    - [PyTube Error `'NoneType' object has no attribute 'span'`](#pytube-error-nonetype-object-has-no-attribute-span)

## Intalling requirements

```
pip install -r requirements.txt
```

## Running

```
python labelwizard.py
```

## Building

```
pyinstaller --onefile labelwizard.py
```

## Known Issues

### PyTube Error `urllib.error.HTTPError: HTTP Error 410: Gone`

Revert PyTube versions.

```
pip uninstall pytube
pip install pytube==11.0.1
```

### PyTube Error `'NoneType' object has no attribute 'span'`

https://github.com/pytube/pytube/issues/1243#issuecomment-1032242549
