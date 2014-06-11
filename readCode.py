import re
from pprint import pprint
import pdb;
from string import Template
import xml.etree.ElementTree as ET
from collections import OrderedDict

defines = {}
fonts = {"[Ficture lightFont]":"HelveticaNeue-Light",
         "[Ficture regularFont]":"HelveticaNeue",
         "[Ficture semiboldFont]":"HelveticaNeue-Medium",
         "[Ficture boldFont]":"HelveticaNeue-Bold",
         "[Ficture lightItalicFont]":"HelveticaNeue-LightItalic",
         "[Ficture italicFont]":"HelveticaNeue-Italic",
         }
objc_file = open("../ios/Shared/MISearchListCell.h")
line = objc_file.readline()
while line:
    line = line.rstrip('\n').strip(' ')
    if line.startswith("#define"):
        components = line.split(' ')
        if len(components) > 2:
            defines[components[1]] = components[2]
    line = objc_file.readline()


objc_file = open("../ios/Shared/MISearchListCell.m")

command = ""

elements = OrderedDict()

empty_line_re = re.compile('^\s+$')
alloc_re = re.compile('(\S+)\s?\=\s?\[\s?\[?\s?(\S+) alloc\s?\]')
button_re = re.compile('(\S+)\s?\=\s?\[UIButton buttonWithType:(\S+)?\s?\]')
add_subview_re = re.compile("\[\s?(\S+)\s+addSubview:\s?(\S+)\s?\]")
image_named_re = re.compile('.*UIImage\s+imageNamed\:\@\"(\S+)?\"\]')
font_re = re.compile("\[UIFont fontWithName\:(.*) size:(\S+)\]")
property_re = re.compile("^(\S+)?\.(\S+)\s?\=\s?(.*)\;")

cgrect_re = re.compile('.*CGRectMake\s?\(\s?([^,]+)\s?,\s?([^,]+)?\s?,\s?([^,]+)?\s?,\s?([^,]+)?\s?\)')

def property_eval(instance, property, code) :

    if property == 'image' :
        image_named_re_match = image_named_re.match(code)
        if image_named_re_match :
            instance[property] = image_named_re_match.group(1)
        else :
            #pdb.set_trace()
            instance[property] = "tt_placeholder"
            print "Failed to read image"

    elif property == 'font' :
        font_re_match = font_re.match(code)
        if font_re_match :
            font_name = font_re_match.group(1)
            font_name = font_name in fonts and fonts[font_name] or font_name[2:-1]
            instance[property] = {'name':font_name,'size':font_re_match.group(2)}
        else :
            pdb.set_trace()
            print "Failed to read font"

    elif property == "text":
        instance[property] = code


line = objc_file.readline()
while line:
    line = line.rstrip('\n').strip(' ')

    if empty_line_re.match(line):
        continue

    if line.startswith("#define"):
        components = line.split(' ')
        if len(components) > 2:
            defines[components[1]] = components[2]

    command += line
    if line.endswith(';') or line.endswith('{'):
        re.sub('\s+', ' ', command)

        match = alloc_re.match(line)
        if match :
            if 'UI' in match.group(2) :
                element_name = match.group(1)
                element_class = match.group(2)
                elements[element_name] = {}
                elements[element_name]['class'] = element_class

                if (element_class == 'UIImageView') :
                    if 'initWithImage:' in command :
                        image_named_re_match = image_named_re.match(command)
                        if not image_named_re_match :
                            pdb.set_trace()
                            print 'Image named re failed'
                        else :
                            elements[element_name]['image'] = image_named_re_match.group(1)

                if 'initWithFrame' in command :
                    cgrect_re_match = cgrect_re.match(command)
                    if not cgrect_re_match :
                        pdb.set_trace()
                        print "CGRect re match failed"
                    else:
                        def convert_value (value) :
                            components = value.split(' ')
                            updated_components = []
                            for component in components :
                                if component not in ['+','-','*','/'] :
                                    component = component in defines and defines[component].replace('f','') or component.replace('f','')
                                updated_components.append(component)

                            result = None
                            try : result = eval(" ".join(updated_components))
                            except : pdb.set_trace()

                            return result

                        elements[element_name]['frame'] = [convert_value(value) for value in cgrect_re_match.groups()]

        else :
            button_re_match = button_re.match(line)
            if button_re_match :
                elements[button_re_match.group(1)] = {}
                elements[button_re_match.group(1)]['class'] = 'UIButton'


            else :
                property_re_match = property_re.match(line)
                if property_re_match :
                    element_name = property_re_match.group(1)
                    if element_name in elements:
                        property_name = property_re_match.group(2)
                        # If property assignment...
                        if not 'property_name' in elements[element_name] :
                            property_eval(elements[element_name], property_name, property_re_match.group(3))

        #print command
        command = ""

    line = objc_file.readline()


pprint(elements)

subviews = ET.Element('subviews')
count = 0
for key,element in elements.iteritems() :

    class_name = element['class'].replace('UI','')
    class_name = class_name[0].lower() + class_name[1:]

    object = ET.SubElement(subviews,class_name)
    object.set('userLabel',key)
    object.set('id','abc-{:02d}-123'.format(count))
    object.set('opaque','NO')
    count += 1


    if element['class'] == 'UIImageView' :
        object.set('contentMode','scaleToFill')

    if 'image' in element :
        object.set('image',element['image']+".png")

    if 'frame' in element:
        ET.SubElement(object, 'rect', attrib={'key': 'frame',
                                              'x': str(element['frame'][0]), 'y': str(element['frame'][1]),
                                              'width': str(element['frame'][2]), 'height': str(element['frame'][3])})

    if 'font' in element:
        ET.SubElement(object, 'fontDescription', attrib={'key': 'fontDescription',
                                                         'name': element['font']['name'],
                                                         'family': 'Helvetica Neue',
                                                         'pointSize': element['font']['size']})

    if 'text' in element:
        object.set('text',element['text'])

    if 'backgroundColor' in element:
        ET.SubElement(object, 'fontDescription', attrib={'key': 'fontDescription',
                                                         'name': element['font']['name'],
                                                         'family': 'Helvetica Neue',
                                                         'pointSize': element['font']['size']})

ET.dump(subviews)

outfile = open("MISearchListCell.xib",'w')
outfile.write(Template(open("template.xib").read()).substitute({'subviews':ET.tostring(subviews), 'connections':"", 'resources':""}))
outfile.close()

