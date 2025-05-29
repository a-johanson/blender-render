# blender-render

Use the Python API of Blender to render mesh data using custom shaders. 
The example fragment shader computes depth, surface orientation, and basic diffuse lighting. 
This data is utilized to draw screen-space hatch lines of the scene with an algorithm following Jobard and Lefer’s paper from 1997 on "Creating Evenly-Spaced Streamlines of Arbitrary Density." 
The hatch lines are added back to the scene as Grease Pencil v3 strokes. 

## Usage

To execute `src/main.py`, copy the content of `src/run_from_blender.py` to the Python console in Blender (adapt `script_path` to point to `src/main.py`).

Developed to work with Blender version `4.4`.

## Development

Install [fake-bpy-module](https://github.com/nutti/fake-bpy-module) for code completion.

### GitHub noreply email
```
git config user.name "a-johanson"
git config user.email "a-johanson@users.noreply.github.com"
```

### GitHub tokens
```
git remote add origin https://a-johanson:<TOKEN>@github.com/a-johanson/blender-render.git
git push -u origin master
```
