#!/usr/bin/python
import os
import commands
import json
import logging

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
        if self.manifest_url != None:
            cmd = 'wget %s -O %s' % (self.manifest_url, self.manifest_json)
            (ret, output) = commands.getstatusoutput(cmd)
            if ret == 0:
                logging.info("It's successful to download manifest file")
                return True
            else:
                logging.error("Test Failed - Failed to download manifest file")
                exit(1)
        else:
            logging.error("Test Failed - Failed to get params : manifest_url")
            exit(1)

    def load_json(self):
        # Get json dir path, set it as output directory
        logging.info('Ready to load json file {0}'.format(self.manifest_json))
        try:
            #load target file
            manifest_content = json.load(open(self.manifest_json, 'r'))
            logging.info('Data type is %s' % type(manifest_content))
            return manifest_content
        except Exception, e:
            logging.error(str(e))
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
            logging.error("Error - Parse json file failed after loading .")
            exit(1)

        logging.info('* Finished to generate rhn xml file successfully!')
        logging.info('* Please check the output directory: %s\n\n' % (self.manifest_xml))

class CDNParseManifestXML(ParseManifestXMLBase):
    def __init__(self, manifest_url, manifest_json, manifest_xml):
        super(CDNParseManifestXML, self).__init__(manifest_url, manifest_json, manifest_xml)
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
            if isinstance(manifest_content,list) == False:
                manifest_content = [manifest_content]

            for data in manifest_content:
            # Dict Key list['cdn','Compose' ,'rhn']
                cdn_data = data["cdn"]["products"]

                if isinstance(cdn_data.keys(), list) == False:
                    logging.error("Failed to get content from package manifest.")
                    exit(1)

                # Prepare to analyze manifest of cdn part
                # Get items from Product ID lists
                for key in cdn_data.keys():
                    oneDict = cdn_data[key]
                    product_id_value = oneDict["Product ID"]
                    product_name_value = oneDict["Name"]
                    platform_value = oneDict["Platform"]
                    if oneDict["Platform Version"] != None and "Platform Version" in oneDict.keys():
                        platform_version_value = oneDict["Platform Version"]
                    product_version_value = oneDict["Product Version"]
                    repo_paths_value = oneDict["Repo Paths"]

                    # XML - create Elements tag = productid
                    productid_item = dom.createElement('productid')
                    # XML - set tag attributes for tag productid
                    if product_id_value:
                        productid_item.setAttribute('value', str(product_id_value))
                    else:
                        productid_item.setAttribute('value', product_name_value)

                    productid_item.setAttribute('name', product_name_value)
                    productid_item.setAttribute('platform', platform_value)
                    if oneDict["Platform Version"] != None and "Platform Version" in oneDict.keys():
                        productid_item.setAttribute('platform_version', platform_version_value)
                    productid_item.setAttribute('product_version', product_version_value)

                    # XML - add child item for root
                    root.appendChild(productid_item)

                    if isinstance(repo_paths_value.keys(),list) == True:
                        # Json parse: add all repo_data in different arch lists
                        basearch_list = []
                        basearch_dict = {}
                        for key in repo_paths_value.keys():
                            basearch_value = repo_paths_value[key]["basearch"]

                            if basearch_value not in basearch_list:
                                basearch_dict[basearch_value] = []
                                basearch_list.append(basearch_value)

                            repo_paths_value[key]["relativeurl"] = key
                            basearch_dict[basearch_value].append(repo_paths_value[key])


                        for basearch_value in basearch_list:
                            # XML - create Element tag = arch
                            arch_item = dom.createElement('arch')
                            arch_item.setAttribute('value', basearch_value)

                            #XML - add child element arch_item for productid_item
                            productid_item.appendChild(arch_item)

                            for repo_dict in basearch_dict[basearch_value]:
                                # XML - create Element tag = repoid
                                repoid_item = dom.createElement('repoid')
                                repoid_name = repo_dict["Label"]
                                repoid_item.setAttribute('value', repoid_name)
                                if "releasever" in repo_dict.keys():
                                    releasever = repo_dict['releasever']
                                    repoid_item.setAttribute('releasever', releasever)
                                # XML - add child Element for arch_item
                                arch_item.appendChild(repoid_item)

                                # XML - create Element tag = relativeurl
                                relativeurl_item = dom.createElement('relativeurl')
                                relativeurl = repo_dict["relativeurl"]
                                relativeurl_text = dom.createTextNode(relativeurl)
                                relativeurl_item.appendChild(relativeurl_text)
                                # XML - add child Element for relativeurl_item
                                repoid_item.appendChild(relativeurl_item)

                                # Json parse: parse each rpm with format %{name} %{version} %{release} %{arch}
                                if isinstance(repo_dict["RPMs"], list) == True and len(repo_dict["RPMs"]) > 0:
                                    # XML - create Element tag = packagename
                                    packagename_item = dom.createElement('packagename')
                                    for rpm_pkg in repo_dict["RPMs"]:
                                        rpm_fmt = parse_nvra(rpm_pkg)
                                        wline = "%s %s %s %s" % (rpm_fmt['name'], rpm_fmt['version'], rpm_fmt['release'], rpm_fmt['arch'])
                                        packagename_text = dom.createTextNode(wline)
                                        packagename_item.appendChild(packagename_text)

                                    # XML - add child Element for packagename_item
                                    repoid_item.appendChild(packagename_item)

            logging.info('Begin to write CDN XML file {0}'.format(self.manifest_xml))
            with open(self.manifest_xml, 'w') as f:
                dom.writexml(f, addindent=' '*4, newl='\n', encoding='utf-8')

        except Exception, e:
            logging.error(str(e))
            logging.error("Error - Parse json file failed after loading .")
            exit(1)

        logging.info('* Finished to generate cdn xml file successfully!')
        logging.info('* Please check the output directory: {0}\n\n'.format(self.manifest_xml))


if __name__ == '__main__':
    manifest_url = "http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json"
    rhn_manifest_json = os.path.join("manifest/rhn_test_manifest.json")
    rhn_manifest_xml = os.path.join("manifest/rhn_test_manifest.xml")
    cdn_manifest_json = os.path.join("manifest/rhn_test_manifest.json")
    cdn_manifest_xml = os.path.join("manifest/rhn_test_manifest.xml")
    RHNParseManifestXML(manifest_url, rhn_manifest_json, rhn_manifest_xml).parse_json_to_xml()
    RHNParseManifestXML(manifest_url, cdn_manifest_json, cdn_manifest_xml).parse_json_to_xml()

