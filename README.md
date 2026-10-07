# kp-index-applet

A simple MATE panel applet that displays the last few values of the NOAA Planetary K-index as a graph of color bars.

The Kp index measures the level of geomagnetic activity on a scale from 0 to 9, and is used to help skywatchers determine
the best time to see the *Aurora Borealis* (Northern Lights). The higher the index, the more likely you are to see them.


## Installation

As root/superuser:


```
cp org.mate.panel.applet.KpIndexAppletFactory.service  /usr/share/dbus-1/services/
cp org.mate.panel.KpIndexApplet.mate-panel-applet  /usr/share/mate-panel/applets/
cp kp-index-applet.py  /usr/libexec/
```


## Adding the applet to mate-panel

- Right click on the panel
- Select "Add to panel"
- Type "kp" in the search box (or scroll) and select "Kp index"


If you need to refresh mate-panel after installing:

```
mate-panel --replace &
```


## Build installable rpm


```
rpmbuild -ba kp-index-applet.spec --define "_sourcedir $(pwd)"
```

Install with:


```
rpm -Uvh ~/rpmbuild/RPMS/noarch/kp-index-applet-*-noarch.rpm
```

(or wherever your rpmbuild wrote the rpm to)
