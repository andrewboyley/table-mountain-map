# Terrain 3D Scene Specification

## Purpose

Defines the saved 3D map view configuration used for the point-of-view render,
so that the terrain, camera and lighting setup is reproducible from the project
file rather than reassembled by hand each time.

## Requirements

### Requirement: Terrain derives from the project DEM

The 3D view SHALL take its terrain elevation from a DEM present in the project,
rather than from a flat plane or an online elevation service.

#### Scenario: Terrain is not flat

- **WHEN** the 3D view is opened
- **THEN** the terrain surface shows elevation variation
- **AND** the elevation source is the project's DEM layer

#### Scenario: Elevation source is identifiable

- **WHEN** the terrain settings are inspected
- **THEN** the raster layer supplying elevation is named
- **AND** the band used for elevation is identifiable

### Requirement: Terrain resolution is expressed in linear units

Terrain tiling parameters SHALL be interpreted in the project's linear
coordinate system, so that their numeric values correspond to metres on the
ground.

#### Scenario: Ground error is in metres

- **WHEN** the maximum ground error setting is read
- **THEN** it is a value in metres appropriate for `EPSG:32734`
- **AND** it is not a value that would be degenerate in degrees

#### Scenario: Terrain detail is not pinned coarse

- **WHEN** the view is moved close to the ground
- **THEN** terrain tiles refine beyond the coarsest level
- **AND** the refinement is not blocked by a minimum-parameter floor

### Requirement: Camera is positionable by map coordinates

The 3D camera position and orientation SHALL be settable from explicit map
coordinates, and those values SHALL persist in the project.

#### Scenario: Camera placement is reproducible

- **WHEN** a camera pose is entered as map coordinates and heading
- **THEN** the view moves to that pose
- **AND** reopening the project restores the same pose

#### Scenario: Pose is stored, not just applied

- **WHEN** the project is saved after a camera move
- **THEN** the saved project contains the camera pose
- **AND** it is restored without manual re-entry

### Requirement: Lighting and surface appearance are configurable

The 3D view SHALL allow the scene's surface appearance and environmental
lighting to be configured, and SHALL retain that configuration in the project.

#### Scenario: Materials carry texture

- **WHEN** a material is applied to terrain or an overlay
- **THEN** base colour, metalness and roughness are independently settable
- **AND** an image texture can be bound to the base colour

#### Scenario: Environmental lighting is selectable

- **WHEN** a skybox or other environment source is chosen
- **THEN** the scene is lit by it
- **AND** the choice persists in the project

#### Scenario: 3D symbols can be categorised

- **WHEN** a 3D symbol layer is rendered
- **THEN** its appearance can vary by an attribute
- **AND** the categorisation is retained in the project

### Requirement: Post-processing is configurable and retained

Post-processing effects SHALL be configurable and SHALL persist in the project.

#### Scenario: Effects apply and survive reload

- **WHEN** colour grading, bloom or anti-aliasing is enabled
- **THEN** the effect applies to the rendered view
- **AND** the setting is still in effect after the project is reopened

#### Scenario: Effects can be disabled

- **WHEN** an effect is disabled
- **THEN** the view renders without it
- **AND** the other enabled effects are unaffected
