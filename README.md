# Label-Wizard

Downloads YouTube videos to annotate with bounding boxes for object detection.

![alt text](https://github.com/joshwinebrener/label-wizard/blob/master/screenshot.png?raw=true)

- [Label-Wizard](#label-wizard)
  - [Intalling requirements](#intalling-requirements)
  - [Running](#running)
  - [Building](#building)
  - [Known Issues](#known-issues)
    - [PyTube Error `'NoneType' object has no attribute 'span'`](#pytube-error-nonetype-object-has-no-attribute-span)
    - [PyTube Error `get_throttling_function_name: could not find match for multiple`](#pytube-error-get_throttling_function_name-could-not-find-match-for-multiple)

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

### PyTube Error `'NoneType' object has no attribute 'span'`

https://github.com/pytube/pytube/issues/1243#issuecomment-1032242549

### PyTube Error `get_throttling_function_name: could not find match for multiple`

```
https://stackoverflow.com/a/71890638
```
