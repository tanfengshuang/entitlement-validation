try:
        from xml.etree import ElementTree
except:
        from elementtree import ElementTree


class ReadRHNXML(object):
    def get_channel_list(self, manifest_file):
        doc = ElementTree.parse(manifest_file)
        root = doc.getroot()
        channel_list = [i.get("value") for i in root.findall('repoid')]
        return channel_list

    def get_packages(self, manifest_file, channel):
        doc = ElementTree.parse(manifest_file)
        root = doc.getroot()
        package_list = []
        for i in root.findall('repoid'):
            if i.get("value") == channel:
                for p in i.findall('packagename'):
                    package_list = [s.strip().split(" ")[0] for s in p.text.strip().split("\n") if s.strip() != ""]
                break
        return package_list


class ReadCDNXML(object):
    pass
