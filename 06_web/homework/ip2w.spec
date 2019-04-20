License:        BSD
Vendor:         Otus
Group:          PD01
URL:            http://otus.ru/lessons/3/
Source0:        otus-%{current_datetime}.tar.gz
BuildRoot:      %{_tmppath}/otus-%{current_datetime}
Name:           ip2w
Version:        0.0.1
Release:        1
BuildArch:      noarch
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
BuildRequires: systemd
Requires: python python-requests uwsgi uwsgi-plugin-python2 uwsgi-logger-file
Summary: Weather daemon


%description
Python uWSGI application that returns the weather by specified ip address.
Git version: %{git_version} (branch: %{git_branch})

%define __etcdir        /usr/local/etc
%define __logdir        /var/log/%{name}
%define __rundir        /var/run/%{name}
%define __bindir        /usr/local/%{name}
%define __systemddir    /usr/lib/systemd/system/

%prep
%setup -q -n otus-%{current_datetime}


%install
[ "%{buildroot}" != "/" ] && rm -fr %{buildroot}
%{__mkdir} -p %{buildroot}/%{__logdir}
%{__mkdir} -p %{buildroot}/%{__rundir}
%{__mkdir} -p %{buildroot}/%{__bindir}
%{__install} -m 644 %{name}.py* %{buildroot}/%{__bindir}/
%{__install} -m 644 %{name}.ini %{buildroot}/%{__bindir}/
%{__install} -pD -m 644 %{name}.conf %{buildroot}/%{__etcdir}/%{name}.conf
%{__install} -pD -m 644 %{name}.service %{buildroot}/%{__systemddir}/%{name}.service


%post
%systemd_post %{name}.service
systemctl daemon-reload

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service

%clean
[ "%{buildroot}" != "/" ] && rm -fr %{buildroot}

%files
%dir %{__logdir}
%dir %{__rundir}
%{__bindir}/%{name}.py*
%{__bindir}/%{name}.ini
%{__etcdir}/%{name}.conf
%{__systemddir}/%{name}.service
