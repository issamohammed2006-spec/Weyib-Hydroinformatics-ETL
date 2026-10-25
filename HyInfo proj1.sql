USE weyib_hydro;

-- 1. Update Alemkerem (Exact DMS converted to Decimal + Exact Elevation)
UPDATE station 
SET latitude = 6.983333, longitude = 40.966667, elevation_m = 2712.0 
WHERE station_id = 'ALEMKEREM';

-- 2. Update the Climate Stations' Elevations
UPDATE station SET elevation_m = 2550 WHERE station_id = 'AGARFA';
UPDATE station SET elevation_m = 2480 WHERE station_id = 'ROBE';
UPDATE station SET elevation_m = 3072 WHERE station_id = 'DINSHO';
UPDATE station SET elevation_m = 2400 WHERE station_id = 'SINANA';