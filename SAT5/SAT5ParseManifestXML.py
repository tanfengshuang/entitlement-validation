#!/usr/bin/python
import os
import json
import logging
import commands
import traceback

from xml.dom import minidom

# Create logger
logger = logging.getLogger("entLogger")


try:
    from kobo.rpmlib import parse_nvra
except ImportError:
    logger.info('Need to install packages kobo kobo-rpmlib koji firstly')


class ParseManifestXMLBase(object):
    def __init__(self, manifest_url, cdn_manifest_path, manifest_json, manifest_xml):
        self.manifest_url = manifest_url
        self.manifest_xml = manifest_xml
        self.manifest_json = manifest_json
        self.cdn_manifest_path = cdn_manifest_path

        if not os.path.exists(self.cdn_manifest_path):
            os.mkdir(self.cdn_manifest_path)

    def downloade_manifest(self):
        if self.manifest_url != "":
            cmd = 'wget %s -O %s' % (self.manifest_url, self.manifest_json)
            logger.info("# {0}".format(cmd))
            (ret, output) = commands.getstatusoutput(cmd)
            logger.info(output)
            if ret == 0:
                logger.info("It's successful to download manifest file")
                return True
            else:
                logger.error("Test Failed - Failed to download manifest file")
                return False
        else:
            logger.error("Test Failed - Failed to get testing parameter Manifest_URL.")
            return False

    def load_json(self):
        # Get json dir path, set it as output directory
        logger.info('Ready to load json file {0}'.format(self.manifest_json))
        try:
            # Load target file
            manifest_content = json.load(open(self.manifest_json, 'r'))
            logger.info('Data type is {0}'.format(type(manifest_content)))
            return manifest_content
        except Exception, e:
            logger.error(str(e))
            logger.error("ERROR - Failed to load json file when call json.load().")
            logger.error(traceback.format_exc())
            assert False, str(e)

class SAT5ParseManifestXML(ParseManifestXMLBase):
    def __init__(self, manifest_url, cdn_manifest_path, manifest_json, manifest_xml):
        super(SAT5ParseManifestXML, self).__init__(manifest_url, cdn_manifest_path, manifest_json, manifest_xml)
        self.manifest_url = manifest_url
        self.manifest_xml = manifest_xml

    def parse_json_to_xml(self):
        result = self.downloade_manifest()
        assert result is True, "Failed to download package manifest."

        manifest_content = self.load_json()
        try:
            # XML - create a Dom object
            impl = minidom.getDOMImplementation()
            dom = impl.createDocument(None, 'rhel', None)
            root = dom.documentElement

            # Get Dict content
            if isinstance(manifest_content, list) == False:
                manifest_content = [manifest_content]

            for data in manifest_content:
            # Dict Key list['cdn','Compose' ,'rhn']
                sat5_data = data["rhn"]["channels"]
                if isinstance(sat5_data.keys(), list) == False:
                    assert False, "Failed to get content from package manifest."

                # Prepare to analyze manifest of rhn part for SAT5 testing
                for key in sat5_data.keys():
                    # XML - create Elements tag = repoid
                    repoid_item = dom.createElement('repoid')
                    repoid_item.setAttribute('value', str(key))
                    # XML - add child Element for repoid_item
                    root.appendChild(repoid_item)

                    # XML - create Elements tag = packagename
                    if isinstance(sat5_data[key], list) == True and len (sat5_data[key]) > 0:
                        packagename_item = dom.createElement('packagename')
                        for rpm in sat5_data[key]:
                            rpm_fmt = parse_nvra(rpm)
                            wline = "%s %s %s %s" % (rpm_fmt['name'], rpm_fmt['version'], rpm_fmt['release'], rpm_fmt['arch'])
                            packagename_text = dom.createTextNode(wline)
                            packagename_item.appendChild(packagename_text)
                        # XML - add child Element for packagename_item
                        repoid_item.appendChild(packagename_item)

                logger.info('Begin to write XML file {0} for SAT5.'.format(self.manifest_xml))
                with open(self.manifest_xml, 'w') as f:
                    dom.writexml(f, addindent=' '*4, newl='\n', encoding='utf-8')
        except Exception, e:
            logger.error(str(e))
            logger.error("ERROR - Failed to parse json file when load it.")
            logger.error(traceback.format_exc())
            assert False, str(e)

        logger.info('* Succeed to generate xml file for Satellite5 testing!')
        logger.info('* Please check the output directory: {0}\n\n'.format(self.manifest_xml))


if __name__ == '__main__':
    manifest_url = "http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json"
    cdn_manifest_path = os.path.join(os.getcwd(), "manifest")
    sat5_manifest_json = os.path.join(cdn_manifest_path, "sat5_test_manifest.json")
    sat5_manifest_xml = os.path.join(cdn_manifest_path, "sat5_test_manifest.xml")
    SAT5ParseManifestXML(manifest_url, cdn_manifest_path, sat5_manifest_json, sat5_manifest_xml).parse_json_to_xml()

