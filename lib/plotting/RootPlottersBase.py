#! /usr/bin/env python
from ROOT import *
import ROOT
from array import array
import shutil, os
import pprint
from lib.util.RootAttributeTranslator import *
from lib.util.Logger import *
import lib.util.MiscTools as misctools
from lib.RootHelpers.RootHelperBase import RootHelperBase

class RootPlottersBase(RootHelperBase):
  """Class as a base class for many plotters containing the structure, common functions...
  """

  def __init__(self,name = "plotters_base_functionality" ):
        self.log = Logger().getLogger(self.__class__.__name__, 10)
        self.name = name
        #ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include/");
        #ROOT.gROOT.ProcessLine(".L tdrstyle.cc")
        #from ROOT import setTDRStyle
        #ROOT.setTDRStyle(True)

        #ROOT.gStyle.SetPalette(1)
        #ROOT.gStyle.SetOptStat(0)
        self.copy_to_web_dir = False
        self.webdir = ""
        self.save_extensions = ['png','pdf','eps']
        #self.pp = pprint.PrettyPrinter(indent=4)

  def setName(self, newname): self.name = newname

  def make_plot(self, data):
        print "This is a default method for plotters. It has to be implemented in derived classes"
        pass

  def setCopyToWebDir(self,doCopy=False,webdir=""):
        if doCopy:
            self.copy_to_web_dir = True
            if webdir:
                self.webdir = webdir
            else:
                raise ValueError, "You have to provide a webdir path if you want to copy the files."
        else:
            self.copy_to_web_dir = False
            self.webdir = ""
        return 0

  def get_webdir(self):
        return self.webdir

  def copy_index_html(self, full_path_dir):
        """
        Walk to all subdirs and put index.php if not present.
        """
        for root, dirs, files in os.walk(full_path_dir):
            #print root
            if not os.path.exists("{0}/index.php".format(root)) :
                #shutil.copy("/afs/cern.ch/user/r/roko/www/html/index.php",root)
                self.put_index_php_structure(root)



  def doCopyToWebDir(self,file_name, newname=""):
        if newname=="":
            newname = file_name
        if self.webdir :
            full_path = self.webdir+"/"+newname
            full_path_dir =  os.path.dirname(full_path)
            #misctools.make_sure_path_exists(self.webdir)
            misctools.make_sure_path_exists(full_path_dir)
            #if not os.path.exists("{0}/index.php".format(self.webdir)) :
            self.copy_index_html(self.webdir)
            if not os.path.exists("{0}/index.php".format(full_path_dir)) :
                #shutil.copy("/afs/cern.ch/user/r/roko/www/html/index.php",full_path_dir)
                self.put_index_php_structure(full_path_dir)
            self.log.debug("Copying {0} to webdir {1}".format(file_name,full_path))
            shutil.copy(file_name,full_path)
            self.log.info("Copied {0} to webdir {1}".format(file_name,full_path))
        else :
            raise ValueError, "You have to provide a webdir path if you want to copy the files."
        return 0


  def save(self, canv, plot_name, extensions=['png','root']):
        #extensions = ['.png','.pdf','.eps','.root']
        if len(extensions)==0:
            extensions=['']
        for ext in extensions:
            postfix = "."+ext
            if ext=='':
                postfix=''
            canv.SaveAs(plot_name+postfix)
            self.log.debug("Saving to: {0}.{1}".format(plot_name,ext))
            if self.copy_to_web_dir :
                self.doCopyToWebDir(plot_name+postfix)


  def XtoNDC(self, x):
        gPad.Update() #this is necessary!
        return (x - gPad.GetX1())/(gPad.GetX2()-gPad.GetX1())


  def YtoNDC(self, y):
        gPad.Update() #this is necessary!
        return (y - gPad.GetY1())/(gPad.GetY2()-gPad.GetY1())

  def get_histDim(self,input_hist):
        n_dim = None
        if (isinstance(input_hist, TH3)): n_dim = 3
        elif (isinstance(input_hist, TH2)): n_dim = 2
        elif (isinstance(input_hist, TH1)): n_dim = 1
        else:
            raise TypeError, '[RootPlottersBase::get_histDim] The input to this function should be a histogram. Check your inputs!'
        return n_dim

  def put_index_php_structure(self, www_dir):
      """
      Copies the structure of index.php file to the www_dir.
      """
      index_php = """
        <html>
            <head>
                        <title><?php echo getcwd(); ?></title>
                        <style type='text/css'>
                                body {
                                    font-family: "Candara", sans-serif;
                                    font-size: 9pt;
                                    line-height: 10.5pt;
                                }
                                div.pic h3 { 
                                    font-size: 11pt;
                                    margin: 0.5em 1em 0.2em 1em;
                                }
                                div.pic p {
                                    font-size: 11pt;
                                    margin: 0.2em 1em 0.1em 1em;
                                }
                                div.pic {
                                    display: block;
                                    float: left;
                                    background-color: white;
                                    border: 1px solid #ccc;
                                    padding: 2px;
                                    text-align: center;
                                    margin: 2px 10px 10px 2px;
                                    -moz-box-shadow: 7px 5px 5px rgb(80,80,80);    /* Firefox 3.5 */
                                    -webkit-box-shadow: 7px 5px 5px rgb(80,80,80); /* Chrome, Safari */
                                    box-shadow: 7px 5px 5px rgb(80,80,80);         /* New browsers */  
                                }
                                a { text-decoration: none; color: rgb(80,0,0); }
                                a:hover { text-decoration: underline; color: rgb(255,80,80); }
                                figure {
                                        display: table;
                                        width: 1px; /* This can be any width, so long as it's narrower than any image */
                                        }
                                img, figcaption {
                                        display: table-row;
                                        }
                        </style>

            </head>


            <body>
                    <h4>&copy G. Petrucciani (CERN), R. Plestina (IHEP-CAS)</h4>

                    <?PHP
                        if (file_exists("title.txt")){
                            $page_title = file_get_contents("title.txt");
                            print "<h1>$page_title</h1>";
                        }
                        print "<h3>".getcwd()."</h3>";
                        if (file_exists("basic.info")){
                            print "<h2><a name='basic_info'>Basic information</a></h2>";
                            $file_handle = fopen("basic.info", "rb");

                            while (!feof($file_handle) ) {
                                    $line_of_text = fgets($file_handle);
                                    $parts = explode('=', $line_of_text);
                                    print $parts[0] . $parts[1]. "<BR>";
                            }
                            fclose($file_handle);
                        }
                    ?>
                    

                    
                    <h2><a name="plots">Plots</a></h2>
                    <p>
                        <form>Filter: 
                            <input type="text" name="match" size="30" value="<?php if (isset($_GET['match'])) print htmlspecialchars($_GET['match']);  ?>" /><input type="Submit" value="Search" />
                        </form>
                    </p>

                    <div>
                            <?PHP
                            // ____________________________________________________________________________________________________________
                            $displayed = array();
                            if ($_GET['noplots']) {
                                print "Plots will not be displayed.\n";
                            } else {
                                $other_exts = array('.pdf', '.cxx', '.eps', '.root', '.txt','.C','.gif');
                                $filenames = glob("*.png"); sort($filenames);
                                foreach ($filenames as $filename) {
                                    if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
                                    array_push($displayed, $filename);
                                    print "<div class='pic'>\n";
                                    print "<h3><a href=\"$filename\">$filename</a></h3>";
        //                             print "<a href=\"$filename\"><img src=\"$filename\" style=\"border: none; width: 300px; \"></a>";
                                    $others = array();
                                    $caption_text = '';
                                    foreach ($other_exts as $ex) {
                                        $other_filename = str_replace('.png', $ex, $filename);
                                        if (file_exists($other_filename)) {
        //                                     array_push($others, "<a class=\"file\" href=\"$other_filename\">[" . $ex . "]</a>");
                                            if ($ex != '.txt') {
                                                array_push($others, "<a class=\"file\" href=\"$other_filename\">[" . $ex . "]</a>");
                                                array_push($displayed, $other_filename);
                                                
                                            }
                                            
                                            else {
                                                $caption_text = file_get_contents($other_filename);
                                            }
                                        }
                                    }
        //                             print "<a href=\"$filename\"><figure><img src=\"$filename\" style=\"border: none; width: 300px; \"><figcaption>$caption_text</figcaption></figure></a>";
                                    print "<figure><a href=\"$filename\"><img src=\"$filename\" style=\"border: none; width: 300px; \"></a><figcaption>$caption_text</figcaption></figure>";
                                    if ($others) print "<p>View as ".implode(', ',$others)."</p>";
                                
                                    
                                    print "</div>";
                                }
                            }
                            // ____________________________________________________________________________________________________________
                            ?>

                    </div>
                    <div style="display: block; clear:both;">
                            <h2><a name="files">Other</a></h2>
                            <ul>
                            <?PHP
                            // ____________________________________________________________________________________________________________
                            foreach (glob("*") as $filename) {
                                if ($_GET['noplots'] || !in_array($filename, $displayed)) {
                                    if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
                                    if ($filename=='index.php') continue;
                                    if (is_dir($filename)) {
                                        print "<b><li><a href=\"$filename\">$filename</a></li></b>";

                                    } else {
                                        print "<li><a href=\"$filename\">$filename</a></li>";
                                    }
                                }
                            }
                            // ____________________________________________________________________________________________________________
                            ?>
                            </ul>
                    </div>
        
            </body>
        </html>

            """
      with open(www_dir+'/index.php','w') as f:
          f.write(index_php)
          
            