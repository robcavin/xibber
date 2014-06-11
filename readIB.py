import xml.etree.ElementTree as ET
tree = ET.parse('MIWaterfallCell~ipad.xib')
root = tree.getroot()

index = 0
properties = {}

def find_connections(node) :
  global properties

  if node.tag == 'outlet' :
    properties[node.get('destination')] = node.get('property')

  for child in node :
    find_connections(child)


def process_node (node, parent, superview) :

  global index
  index += 1 

  if node.tag == 'subviews' :
    superview = parent.tag

  name = None
  if parent is not None :
    name = parent.get('id') in properties and properties[parent.get('id')] or parent.get('userLabel')
    node.name = name

  if node.get('id') and node.tag not in ['action','outlet'] :
    instance_name = node.get('id') in properties and properties[node.get('id')] or node.get('userLabel')
    if instance_name :
      if not instance_name.startswith('_') : instance_name = '_'+instance_name

      class_name = node.tag[0].upper() + node.tag[1:] 
      print ""
      print "UI{}* {} = [[UI{} alloc] init];".format(class_name, instance_name, class_name)
      print "[{} addSubview:{}];".format((parent is not None and 'name' in parent) and parent.name or 'self.view', instance_name)

      if node.tag == 'label' :
        print '{}.text = @"{}";'.format(instance_name, node.get('text'))

      if node.tag == 'imageView' and node.get('image') :
        print '{}.image = [UIImage imageNamed:@"{}"]'.format(instance_name, node.get('image'))

    parent = node
 
  if name :
    if not name.startswith('_') : name = '_'+name

    if node.tag == 'rect' and node.get('key') == 'frame' :
      print "{}.frame = CGRectMake({:.1f}f,{:.1f}f,{:.1f}f,{:.1f}f);".format(name,float(node.get('x')),float(node.get('y')),float(node.get('width')),float(node.get('height')))

    if node.tag == 'action' :
      print "[{} addTarget:self action:@selector({}) forControlEvents:UIControlEventTouchUpInside];".format(name,node.get('selector'))

    if node.tag == 'fontDescription' :
      print '{}.font = [UIFont fontWithName:@"{}" size:{:0.1f}f];'.format(name, node.get('name'),float(node.get('pointSize')))

    if node.tag == 'color' :
      if node.get('colorSpace') == "deviceRGB" :
        print '{}.{} = [UIColor colorWithRGBHex:0x{:02x}{:02x}{:02x} withAlpha:{:.1f}f];'.format(name,node.get('key'),int(float(node.get('red'))*255.0), int(float(node.get('red'))*255.0), int(float(node.get('red'))*255.0), float(node.get('alpha')))
      elif node.get('colorSpace') == 'calibratedWhite' :
        print '{}.{} = [UIColor colorWithRGBHex0x:{:02x}{:02x}{:02x} withAlpha:{:.1f}f];'.format(name,node.get('key'),int(float(node.get('white'))*255.0), int(float(node.get('white'))*255.0), int(float(node.get('white'))*255.0), float(node.get('alpha')))
      else : print "UNKNOWN COLOR FORMAT"

  for child in node :
     process_node(child, parent, superview)


find_connections(root.find('objects'))
process_node(root.find('objects'), None, None)
