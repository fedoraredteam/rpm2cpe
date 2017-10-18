import re
import argparse
import json
import subprocess
import sys
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

    def pieces(self):
        package_name = []
        release = None
        architecture = None
        major = None
        minor = None
        micro = None
        special = None

        pieces = re.split(r"(^\d*\D+\d*)(?=-\d)", self.rpm_name)
        if pieces[0]:
            smaller_pieces = re.findall(r"([a-zA-Z1-9\-_]+)", pieces[0], re.X)
            package_name = smaller_pieces[0]
            if len(smaller_pieces) == 3:
                release = smaller_pieces[1]
                architecture = smaller_pieces[2]
            elif len(smaller_pieces) == 2:
                architecture = smaller_pieces[1]
        elif pieces[1]:
            package_name = pieces[1]
            for smaller_piece in re.findall(r"([a-zA-Z1-9_]+)", pieces[2], re.X):
                if smaller_piece in self.valid_archs:
                    architecture = smaller_piece
                elif smaller_piece in self.valid_releases:
                    release = smaller_piece
                elif not major:
                    major = smaller_piece
                elif not minor:
                    minor = smaller_piece
                elif not micro:
                    micro = smaller_piece
                elif not special:
                    special = smaller_piece

        return package_name, major, minor, micro, special, release or "*", architecture or "*"

    def cpe(self):
        versions = []
        cpe_strings = []
        name, major, minor, micro, special, release, architecture = self.pieces()
        # We will build one version string if 'strict' is required
        if self.strict:
            version = major
            if minor:
                version += '.'
                version += minor
            if micro:
                version += '.'
                version += micro
            if special:
                version += '-'
                version += special
            versions.append(version)
        else:
            version = major
            versions.append(version)
            if minor:
                version += '.'
                version += minor
                versions.append(version)
            if micro:
                version += '.'
                version += micro
                versions.append(version)
            if special:
                version += '-'
                version += special
                versions.append(version)

        # Now we build the answers
        for version in versions:
            cpe = ['cpe:/a']
            cpe.append('*')  # Vendor
            cpe.append(name) # Package Name
            cpe.append(version)
            if self.release_info:
                cpe.append(release)
            if self.arch_info:
                cpe.append(architecture)
            try:
                cpe_strings.append(':'.join(cpe))
            except TypeError:
                cpe_strings.append("error: " + self.rpm_name)
        return cpe_strings

    def __iter__(self):
        yield (self.rpm_name, self.cpe())

    def __str__(self):
        if len(self.cpe()) > 1:
            return '\n'.join(self.cpe())
        return ''.join(self.cpe())

    def csv(self):
        line_start = '\n' + self.rpm_name + ','
        if len(self.cpe()) > 1:
            return line_start.join(self.cpe())
        return self.rpm_name + ',' + self.cpe()[0]

    def json(self, pretty=False):
        if pretty:
            return json.dumps(dict(self), indent=4, sort_keys=True)
        return json.dumps(dict(self))

class Repo(object):
    def __init__(self, name, strict=False):
        self.name = name
        self.rpms = []
        self.strict = strict

    def _get_rpms(self):
        try:
            command = ["yum", "list", "available", 
                       "--enablerepo=" + self.name,
                       "--showduplicates"]
            p = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            lines = out.split('\n')
            error_lines = err.split('\n')
        except OSError:
            sys.exit(1)
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
        self._get_rpms()
        for rpm in self.rpms:
            cpes.append(rpm.cpe())    
        flat_list = [item for sublist in cpes for item in sublist]
        return '\n'.join(flat_list)

    def __iter__(self):
        self._get_rpms()
        repo_dict = dict()
        for rpm in self.rpms:
            repo_dict.update(dict(rpm))
        yield(self.name, repo_dict)

    def json(self, pretty=False):
        if pretty:
            return json.dumps(dict(self), indent=4, sort_keys=True)
        return json.dumps(dict(self))

    def csv(self):
        lines = []
        self._get_rpms()
        line_start = self.name + ','
        for rpm in self.rpms:
            for line in rpm.csv().split('\n'):
                lines.append(line_start + line)
        return '\n'.join(lines)


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
