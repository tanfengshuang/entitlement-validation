import logging
import traceback

try:
        from xml.etree import ElementTree
except:
        from elementtree import ElementTree


class ReadRHNXML(object):
    def get_channel_list(self, manifest_xml):
        doc = ElementTree.parse(manifest_xml)
        root = doc.getroot()
        channel_list = [i.get("value") for i in root.findall('repoid')]
        return channel_list

    def get_package_list(self, manifest_xml, channel):
        doc = ElementTree.parse(manifest_xml)
        root = doc.getroot()
        package_list = []
        for i in root.findall('repoid'):
            if i.get("value") == channel:
                for p in i.findall('packagename'):
                    package_list = [s.strip().split()[0] for s in p.text.strip().splitlines() if s.strip() != ""]
                break
        return package_list


class ReadCDNXML(object):
    def get_element(self, ele, tags):
        for tag in tags:
            ele = self.get_next_element(ele, tag)
            if ele != None:
                continue
            else:
                logging.error("There is no element {0} in manifest.".format(tag))
                exit(1)
        return ele

    def get_next_element(self, ele, tag):
        # get next element instance
        for i in list(ele):
            if i.get('value') == tag:
                return i

    def get_repoid_element(self, manifest_xml, args):
        doc = ElementTree.parse(manifest_xml)
        root_ele = doc.getroot()
        if root_ele != None:
            repoid_ele = self.get_element(root_ele, args)
            return repoid_ele
        else:
            logging.error("There is no rhel root element in manifest.")
            exit(1)

    def get_repo_list(self, manifest_xml, release_ver, *args):
        # args: (pid, current_arch)
        try:
            repoid_ele = self.get_repoid_element(manifest_xml, args)
            repo_list = [i.get("value") for i in repoid_ele.findall("repoid") if i.get("releasever") == release_ver]
            return repo_list
        except Exception, e:
            logging.error(str(e))
            logging.error(traceback.format_exc())
            logging.error("Test Failed - Raised error when get repo list from cdn xml manifest!")
            exit(1)

    def get_package_list(self, manifest_xml, repo, release_ver, *args):
        # args: (pid, current_arch)
        try:
            repoid_ele = self.get_repoid_element(manifest_xml, args)

            package_list = []
            for i in repoid_ele.findall("repoid"):
                if i.get("releasever") == release_ver and i.get('value') == repo:
                    package_list = [j.text.strip().splitlines() for j in list(i) if j.tag == "packagename"]
            return [i.strip() for i in package_list[0]]
        except Exception, e:
            logging.error(str(e))
            logging.error(traceback.format_exc())
            logging.error("Test Failed - Raised error when get package list from cdn xml manifest!")
            exit(1)

if __name__ == "__main__":
    # 69 x86_64 rhel-6-server-debug-rpms 6Server
    repolist = ReadCDNXML().get_repo_list("manifest/cdn_test_manifest.xml", "6Server", "69", "x86_64")
    pkg_list = ReadCDNXML().get_package_list("manifest/cdn_test_manifest.xml", "rhel-6-server-debug-rpms", "6Server", "69", "x86_64")
    print repolist
    print pkg_list
