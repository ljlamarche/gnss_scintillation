# ipp_utils.py
# Utilities for calculating ionospheric pierce points

import numpy as np
import datetime as dt
import pymap3d as pm

def projalt(site,az,el,proj_alt=300.):

    lat0, lon0, alt0 = site
    az = az*np.pi/180.
    el = el*np.pi/180.

    x, y, z = pm.geodetic2ecef(lat0, lon0, alt0)
    vx, vy, vz = pm.enu2uvw(np.cos(el)*np.sin(az), np.cos(el)*np.cos(az), np.sin(el), lat0, lon0)

    earth = pm.Ellipsoid()
    a2 = (earth.semimajor_axis + proj_alt*1000.)**2
    b2 = (earth.semimajor_axis + proj_alt*1000.)**2
    c2 = (earth.semiminor_axis + proj_alt*1000.)**2

    A = vx**2/a2 + vy**2/b2 + vz**2/c2
    B = x*vx/a2 + y*vy/b2 + z*vz/c2
    C = x**2/a2 + y**2/b2 + z**2/c2 -1

    alpha = (np.sqrt(B**2-A*C)-B)/A

    lat, lon, alt = pm.ecef2geodetic(x + alpha*vx, y + alpha*vy, z + alpha*vz)

    return lat, lon, alt/1000.


def calc_ipp(site, sat_ephem, height=300.):
    lat0, lon0, alt0 = site
    x, y, z = pm.geodetic2ecef(lat0, lon0, alt0)

    vx = sat_ephem[0] - x
    vy = sat_ephem[1] - y
    vz = sat_ephem[2] - z

    earth = pm.Ellipsoid()
    a2 = (earth.semimajor_axis + height*1000.)**2
    b2 = (earth.semimajor_axis + height*1000.)**2
    c2 = (earth.semiminor_axis + height*1000.)**2

    A = vx**2/a2 + vy**2/b2 + vz**2/c2
    B = x*vx/a2 + y*vy/b2 + z*vz/c2
    C = x**2/a2 + y**2/b2 + z**2/c2 -1

    alpha = (np.sqrt(B**2-A*C)-B)/A

    lat, lon, alt = pm.ecef2geodetic(x + alpha*vx, y + alpha*vy, z + alpha*vz)

    return lat, lon, alt/1000.

def gaussiran_method(site, az, el, height=300.):

    lat0, lon0, alt0 = site
    phi0 = lat0*np.pi/180.
    lam0 = lon0*np.pi/180.
    az = az*np.pi/180.
    el = el*np.pi/180.
    RE = 6371.

    p = np.pi/2-el-np.arcsin(RE*np.cos(el)/(RE+height))

    phi = np.arcsin(np.sin(phi0)*np.cos(p)+np.cos(phi0)*np.sin(p)*np.cos(az))
    lam = lam0 + np.arcsin(np.sin(p)*np.sin(az)/np.cos(phi0))

    return phi*180./np.pi, lam*180./np.pi



def parse_sp3(filename):
    sat_ephem = {}
    time = []

    with open(filename,'r') as sp3file:
        lines = sp3file.readlines()
        num_sat = int(lines[2].split()[1])

        for s in range(num_sat):
            sat_ephem['{:02}'.format(s+1)] = []

        for j in range(22,len(lines)-1,num_sat+1):

            t = lines[j][2:-6]
            time.append(dt.datetime.strptime(t, ' %Y %m %d %H %M %S.%f'))

            for i in range(num_sat):
                s = lines[j+i+1].split()
                sat_ephem[s[0][2:]].append([float(s[1]),float(s[2]),float(s[3])])

    for sat in sat_ephem:
        sat_ephem[sat] = np.array(sat_ephem[sat]).T*1000.

    return sat_ephem, np.array(time)
