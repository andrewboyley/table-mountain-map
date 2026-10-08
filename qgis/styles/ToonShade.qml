<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis autoRefreshMode="Disabled" autoRefreshTime="0" hasScaleBasedVisibilityFlag="0" layerType="Raster" maxScale="0" minScale="1e+08" styleCategories="Symbology|Symbology3D|Fields|Forms|Actions|Diagrams|Rendering|GeometryOptions|Relations" version="4.2.2-Belém do Pará">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option name="name" type="QString" value=""/>
      <Option name="properties"/>
      <Option name="type" type="QString" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling enabled="false" maxOversampling="2" zoomedInResamplingMethod="cubic" zoomedOutResamplingMethod="cubic"/>
    </provider>
    <rasterrenderer alphaBand="-1" band="1" classificationMax="251.1244659" classificationMin="10.3525763" nodataColor="" opacity="1" type="singlebandpseudocolor">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="2" clip="0" colorRampType="DISCRETE" labelPrecision="0" maximumValue="251.12446589999999" minimumValue="10.352576300000001">
          <colorramp name="[source]" type="gradient">
            <Option type="Map">
              <Option name="color1" type="QString" value="0,0,0,128,rgb:0,0,0,0.5000076"/>
              <Option name="color2" type="QString" value="255,255,255,255,hsv:0,0,1,1"/>
              <Option name="direction" type="QString" value="ccw"/>
              <Option name="discrete" type="QString" value="1"/>
              <Option name="rampType" type="QString" value="gradient"/>
              <Option name="spec" type="QString" value="rgb"/>
              <Option name="stops" type="QString" value="0.25;128,128,128,128,hsv:0,0,0.50000762939453125,0.50000762939453125;rgb;ccw:0.5;255,255,255,255,hsv:0,0,1,1;rgb;ccw"/>
            </Option>
          </colorramp>
          <item alpha="128" color="#000000" label="&lt;= 71" value="70.5455487"/>
          <item alpha="128" color="#808080" label="71 - 131" value="130.73852109999999"/>
          <item alpha="255" color="#ffffff" label="131 - 191" value="190.9314935"/>
          <item alpha="255" color="#ffffff" label="> 191" value="inf"/>
          <rampLegendSettings direction="0" maximumLabel="" minimumLabel="" orientation="2" prefix="" suffix="" useContinuousLegend="1">
            <numericFormat id="basic">
              <Option type="Map">
                <Option name="decimal_separator" type="invalid"/>
                <Option name="decimals" type="int" value="6"/>
                <Option name="rounding_type" type="int" value="0"/>
                <Option name="show_plus" type="bool" value="false"/>
                <Option name="show_thousand_separator" type="bool" value="true"/>
                <Option name="show_trailing_zeros" type="bool" value="false"/>
                <Option name="thousand_separator" type="invalid"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation colorizeBlue="128" colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeStrength="100" grayscaleMode="0" invertColors="0" saturation="0"/>
    <rasterresampler maxOversampling="2" zoomedInResampler="cubic" zoomedOutResampler="cubic"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>6</blendMode>
</qgis>
