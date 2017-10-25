import re
import argparse
import json
import subprocess

class Cpe(object):
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.vulnerable = True
    
    def cpeMatchString(self):
        cpe = ['cpe:/a']
        cpe.append('*')  # Vendor
        cpe.append(self.name) # Package Name
        cpe.append(self.version)
        return ':'.join(cpe)

    def cpe23Uri(self):
        cpe = ['cpe:2.3:a']
        cpe.append('*')
        cpe.append(self.name)
        cpe.append(self.version)
        cpe.append('*:*:*:*:*:*:*')
        return ':'.join(cpe)

    def __str__(self):
        return self.cpeMatchString() + ',' + self.cpe23Uri()



class Rpm(object):
    valid_archs = ['i386', 'i486', 'i586', 'i686', 'athlon', 'geode', 'pentium3',
                   'pentium4', 'x86_64', 'amd64', 'ia64', 'alpha', 'alphaev5',
                   'alphaev56', 'alphapca56', 'alphaev6', 'alphaev67', 'sparc',
                   'sparcv8', 'sparcv9', 'sparc64', 'sparc64v', 'sun4', 'sun4c',
                   'sun4d', 'sun4m', 'sun4u', 'armv3l', 'armv4b', 'armv4l',
                   'armv5tel', 'armv5tejl', 'armv6l', 'armv7l', 'mips', 'mipsel',
                   'ppc', 'ppciseries', 'ppcpseries', 'ppc64', 'ppc8260', 'ppc8560',
                   'ppc32dy4', 'm68k', 'm68kmint', 'atarist', 'atariste', 'ataritt',
                   'falcon', 'atariclone', 'milan', 'hades', 'Sgi', 'rs6000', 'i370',
                   's390x', 's390', 'noarch']

    def __init__(self, rpm_name, strict=False, release_info=False, arch_info=False):
        self.rpm_name = rpm_name.replace('.rpm', '')
        self.strict = strict
        self.release_info = release_info
        self.arch_info = arch_info
        self.valid_releases = []
        for i in range(5, 10):
            self.valid_releases.append("el"+str(i))
        for i in range(17, 30):
            self.valid_releases.append("fc"+str(i))


    def file_name(self):
        return self.rpm_name + '.rpm'

    def get_arch(self):
        for arch in self.valid_archs:
            if arch in self.rpm_name:
                return arch
        return None

    def get_release(self):
        for release in self.valid_releases:
            if release in self.rpm_name:
                match = re.search(r"(" + release + "[^\.]*(?=\.)?)", self.rpm_name)
                return match.group(0)
        return None

    def pieces(self):
        package_name = []
        release = None
        architecture = None
        version = None

        working_string = self.rpm_name
        architecture = self.get_arch()
        release = self.get_release()
        if architecture:
            working_string = working_string.replace('.' + architecture, '')
        if release:
            working_string = working_string.replace('.' + release, '')
        pieces = re.findall(r"([a-zA-Z0-9-]+)(?=-\d)-(\d.*)", working_string, re.X)
        if pieces:
            package_name = pieces[0][0]
            version = pieces[0][1]
        else:
            package_name = working_string
            version = '*'

        return package_name, version, release or "*", architecture or "*"

    def cpes(self):
        versions = []
        cpes = []
        name, version, _, _ = self.pieces()
        versions.append(version)
        # We will build one version string if 'strict' is required
        if not self.strict:
            version_pieces = version.split('.')
            for i in range(1, len(version_pieces)):
                versions.append('.'.join(version_pieces[:i]))

        # Now we build the answers
        for version in versions:
            cpes.append(Cpe(name, version))
            
        return cpes

    def __iter__(self):
        result = []
        for cpe in self.cpes():
            result.append(dict(vulnerable=True,
                                cpeMatchString=cpe.cpeMatchString(),
                                cpe23Uri=cpe.cpe23Uri()))
        yield (self.rpm_name, dict(cpe=result))

    def __str__(self):
        if len(self.cpes()) > 1:
            return '\n'.join([str(cpe) for cpe in self.cpes()])
        return ''.join([str(cpe) for cpe in self.cpes()])

    def csv(self):
        line_start = '\n' + self.rpm_name + ','
        if len(self.cpes()) > 1:
            return self.rpm_name + ',' + line_start.join([str(cpe) for cpe in self.cpes()])
        return self.rpm_name + ',' + [str(cpe) for cpe in self.cpes()][0]

    def json(self, pretty=False):
        if pretty:
            return json.dumps(dict(self), indent=4, sort_keys=True)
        return json.dumps(dict(self))

class Repo(object):
    def __init__(self, name, strict=False):
        self.name = name
        self.rpms = []
        self.strict = strict
        self.el_error_msg = "Unable to obtain repo information.  This is may not be an enterprise Linux host."

    def _get_rpms(self):
        command = ["yum", "makecache", "fast",
                   "--disablerepo=*" 
                   "--enablerepo=" + self.name]
        p = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        
        command = ["yum", "list", "available",
                   "--disablerepo=*" 
                   "--enablerepo=" + self.name,
                   "--showduplicates"]
        p = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = p.communicate()
        lines = out.split('\n')
        error_lines = err.split('\n')

        for index, rpm_line in enumerate(lines):
            try:
                if not re.match(r'^[a-zA-Z0-9]', lines[index+1]) and not index == len(lines) - 1:
                    lines[index] += lines[index+1]
                    lines.pop(index+1)
                rpm_pieces = re.split(r"\s{2,}",lines[index])
                rpm_sub_pieces = rpm_pieces[0].split('.')
                rpm_full = [rpm_sub_pieces[0]]
                rpm_full.append('-')
                rpm_full.append(rpm_pieces[1])
                rpm_full.append('.')
                rpm_full.append(rpm_sub_pieces[1])
                rpm_name = ''.join(rpm_full)
                if rpm_name:
                    self.rpms.append(Rpm(rpm_name, self.strict))
            except IndexError:
                pass

    def __str__(self):
        cpes = []
        try:
            self._get_rpms()
            for rpm in self.rpms:
                cpes.append(rpm.cpe())    
            flat_list = [item for sublist in cpes for item in sublist]
            return '\n'.join(sorted(list(set(flat_list))))
        except OSError as error:
            if error.errno == 2:
                return self.name + ": " + self.el_error_msg
            return self.name + ": " + error

    def __iter__(self):
        try:
            self._get_rpms()
            repo_dict = dict()
            for rpm in self.rpms:
                repo_dict.update(dict(rpm))
            yield(self.name, repo_dict)
        except OSError as error:
            if error.errno == 2:
                yield(self.name, dict(error=self.el_error_msg))
            else:
                yield(self.name, dict(error=str(error)))


    def json(self, pretty=False):
        if pretty:
            return json.dumps(dict(self), indent=4, sort_keys=True)
        return json.dumps(dict(self))

    def csv(self):
        try:
            lines = []
            self._get_rpms()
            line_start = self.name + ','
            for rpm in self.rpms:
                for line in rpm.csv().split('\n'):
                    lines.append(line_start + line)
            return '\n'.join(sorted(list(set(lines))))
        except OSError as error:
            if error.errno == 2:
                return self.name + ',error,' + self.el_error_msg
            return self.name + ',error,' + error


def print_resource(resource, output_format):
    if output_format == 't':
        print str(resource)
    elif output_format == 'j':
        print resource.json(pretty=True)
    elif output_format == 'c':
        print resource.csv()

def main():
    parser = argparse.ArgumentParser(description='Translate an RPM name to CPE.')
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--rpm',
                       help='The RPM name to translate.  Can be a comma separated list.',
                       nargs='+',
                       required=False)
    group.add_argument('--repo',
                        help='If specified, rpm2cpe will translate all RPM\'s to CPE\'s.  Only executeable on an Enterprise Linux Host.',
                        required=False,
                        nargs='+',)
    parser.add_argument('-s','--strict',
                        help='Return multiple CPE strings for a given package version with varying version numbers',
                        required=False,
                        action='store_true')
    output_group = parser.add_mutually_exclusive_group(required=False)
    output_group.add_argument('-t', '--txt', action='store_const', dest='output', const='t')
    output_group.add_argument('-j', '--json', action='store_const', dest='output', const='j')
    output_group.add_argument('-c', '--csv', action='store_const', dest='output', const='c')
    parser.set_defaults(output='c')

    args = parser.parse_args()
    if args.rpm:
        for rpm in args.rpm:
            rpm2cpe = Rpm(rpm, args.strict)
            print_resource(rpm2cpe, args.output)
    elif args.repo:
        for repo_name in args.repo:
            repo = Repo(repo_name, args.strict)
            print_resource(repo, args.output)

if __name__ == '__main__':
    main()
