#!/usr/bin/python
import os
import json
import logging
import commands
import traceback

from xml.dom import minidom

try:
    from kobo.rpmlib import parse_nvra
except ImportError:
    logging.info('Need to install packages kobo kobo-rpmlib koji firstly')


class ParseManifestXMLBase(object):
    def __init__(self, manifest_url, manifest_json, manifest_xml):
        self.manifest_url = manifest_url
        self.manifest_xml = manifest_xml
        self.manifest_json = manifest_json

    def downloade_manifest(self):
        if self.manifest_url != "":
            cmd = 'wget %s -O %s' % (self.manifest_url, self.manifest_json)
            logging.info("# {0}".format(cmd))
            (ret, output) = commands.getstatusoutput(cmd)
            logging.info(output)
            if ret == 0:
                logging.info("It's successful to download manifest file")
                return True
            else:
                logging.error("Test Failed - Failed to download manifest file")
                exit(1)
        else:
            logging.error("Test Failed - Failed to get testing param Manifest_URL.")
            exit(1)

    def load_json(self):
        # Get json dir path, set it as output directory
        logging.info('Ready to load json file {0}'.format(self.manifest_json))
        try:
            # Load target file
            manifest_content = json.load(open(self.manifest_json, 'r'))
            logging.info('Data type is %s' % type(manifest_content))
            return manifest_content
        except Exception, e:
            logging.error(str(e))
            logging.error(traceback.format_exc())
            logging.error("Error - Load json file failed when running json.load() function.")
            exit(1)

class RHNParseManifestXML(ParseManifestXMLBase):
    def __init__(self, manifest_url, manifest_json, manifest_xml):
        super(RHNParseManifestXML, self).__init__(manifest_url, manifest_json, manifest_xml)
        self.manifest_url = manifest_url
        self.manifest_xml = manifest_xml

    def parse_json_to_xml(self):
        self.downloade_manifest()
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
                rhn_data = data["rhn"]["channels"]
                if isinstance(rhn_data.keys(), list) == False:
                    logging.info("Failed to get content from package manifest.")
                    exit(1)
                # Prepare to analyze manifest of rhn part
                for key in rhn_data.keys():
                    # XML - create Elements tag = repoid
                    repoid_item = dom.createElement('repoid')
                    repoid_item.setAttribute('value', str(key))
                    # XML - add child Element for repoid_item
                    root.appendChild(repoid_item)

                    # XML - create Elements tag = packagename
                    if isinstance(rhn_data[key], list) == True and len (rhn_data[key]) > 0:
                        packagename_item = dom.createElement('packagename')
                        for rpm in rhn_data[key]:
                            rpm_fmt = parse_nvra(rpm)
                            wline = "%s %s %s %s" % (rpm_fmt['name'], rpm_fmt['version'], rpm_fmt['release'], rpm_fmt['arch'])
                            packagename_text = dom.createTextNode(wline)
                            packagename_item.appendChild(packagename_text)
                        # XML - add child Element for packagename_item
                        repoid_item.appendChild(packagename_item)

                logging.info('Begin to write RHN XML file %s' % self.manifest_xml)
                with open(self.manifest_xml, 'w') as f:
                    dom.writexml(f, addindent=' '*4, newl='\n', encoding='utf-8')
        except Exception, e:
            logging.error(str(e))
            logging.error(traceback.format_exc())
            logging.error("Error - Parse json file failed after loading .")
            exit(1)

        logging.info('* Finished to generate rhn xml file successfully!')
        logging.info('* Please check the output directory: %s\n\n' % (self.manifest_xml))


if __name__ == '__main__':
    manifest_url = "http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json"
    rhn_manifest_json = os.path.join(os.getcwd(), "manifest/rhn_test_manifest.json")
    rhn_manifest_xml = os.path.join(os.getcwd(), "manifest/rhn_test_manifest.xml")
    cdn_manifest_json = os.path.join(os.getcwd(), "manifest/rhn_test_manifest.json")
    cdn_manifest_xml = os.path.join(os.getcwd(), "manifest/rhn_test_manifest.xml")
    RHNParseManifestXML(manifest_url, rhn_manifest_json, rhn_manifest_xml).parse_json_to_xml()

