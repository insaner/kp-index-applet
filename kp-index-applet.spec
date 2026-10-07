Name:           kp-index-applet
Version:        1.0
Release:        1%{?dist}
Summary:        MATE panel applet showing NOAA Planetary K-index

License:        MIT
URL:            https://github.com/insaner/kp-index-applet

BuildArch:      noarch
Requires:       python3
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       mate-panel


%description
A simple MATE panel applet that displays the last few values of the
NOAA Planetary K-index as a graph of color bars.

%prep
cp %{_sourcedir}/kp-index-applet.py .
cp %{_sourcedir}/org.mate.panel.KpIndexApplet.mate-panel-applet .
cp %{_sourcedir}/org.mate.panel.applet.KpIndexAppletFactory.service .
cp %{_sourcedir}/org.mate.panel.KpIndexApplet.gschema.xml .


%build
# nothing to build

%install
install -D -m 755 kp-index-applet.py \
    %{buildroot}%{_libexecdir}/kp-index-applet.py

install -D -m 644 org.mate.panel.KpIndexApplet.mate-panel-applet \
    %{buildroot}%{_datadir}/mate-panel/applets/org.mate.panel.KpIndexApplet.mate-panel-applet

install -D -m 644 org.mate.panel.applet.KpIndexAppletFactory.service \
    %{buildroot}%{_datadir}/dbus-1/services/org.mate.panel.applet.KpIndexAppletFactory.service

install -D -m 644 org.mate.panel.KpIndexApplet.gschema.xml \
    %{buildroot}%{_datadir}/glib-2.0/schemas/org.mate.panel.KpIndexApplet.gschema.xml


%files
%{_libexecdir}/kp-index-applet.py
%{_datadir}/mate-panel/applets/org.mate.panel.KpIndexApplet.mate-panel-applet
%{_datadir}/dbus-1/services/org.mate.panel.applet.KpIndexAppletFactory.service
%{_datadir}/glib-2.0/schemas/org.mate.panel.KpIndexApplet.gschema.xml

%changelog
* Tue Oct 06 2026 insaner <github-bugs@insaner.com> - 1.0-1
- Initial package
