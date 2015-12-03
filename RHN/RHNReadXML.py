import logging
import traceback

try:
        from xml.etree import ElementTree
except:
        from elementtree import ElementTree


class RHNReadXML(object):
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

if __name__ == "__main__":
    pass
