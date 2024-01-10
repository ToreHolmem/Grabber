import gdal
import osr

# Define the input parameters
center_lat = 62.47481623447284
center_lon = 6.245537627390876
half_size = 0.5 * 1000 / 2  # Set size

min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)

# Convert the bounding box to UTM
src_srs = osr.SpatialReference()
src_srs.ImportFromEPSG(4326)
dst_srs = osr.SpatialReference()
dst_srs.ImportFromEPSG(25833)
transformer = osr.CoordinateTransformation(src_srs, dst_srs)
min_x_utm, min_y_utm, _ = transformer.TransformPoint(min_x, min_y)
max_x_utm, max_y_utm, _ = transformer.TransformPoint(max_x, max_y)

# Define the URL template for the GeocacheTerreng service
url_template = "https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheTerreng/ImageServer/exportImage?bbox={},{},{},{}&bboxSR=25833&imageSR=25833&size=512,512&interpolation=RSP_BilinearInterpolation&format=lerc&f=image"

# Download the elevation data
url = url_template.format(min_x_utm, min_y_utm, max_x_utm, max_y_utm)
elevation_data = gdal.Open("/vsicurl/{}".format(url))

# Save the elevation data to a GeoTIFF file
gdal.Translate("elevation_data.tif", elevation_data)
