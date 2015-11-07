
import pprint



class WebGalleryMaker(object):
    """
    Makes the web page with figure gallery and filter for figures. 
    """
    def __init__(self):
        pass
        pp = pprint.PrettyPrinter(indent=4)
        self.set_style()
        self._set_web_page()
        self.title = ""
        self.figure_type=".png"
    
    def dump_page(self, dir_path=0):
        pass
        if dir_path == 0:
            pp.pprint(self.web_page)
        ### copy the files from the list to the web location    
            
    
    def set_title(self, title):
        pass
    def set_date(self, date):
        pass
    
    def set_figure_type(self, date):
        pass
    
    def embed_slides(self, path, is_link=0):
        pass
    
    def embed_table(self, table):
        pass
    
    def add_files(self, files):
        """Add files as list or csv. 
           These files will be copied to the webdir.
        """
        pass
    
    
    
    def set_style(self,css_file = None):
        if css_file:
            pass
            
        else:
            self.page_style ="""
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
                            </style>""" % self.__dict__
                            
    def _set_web_page(self):
        
        self.web_page = """
            <html>
                <head>
                            <title><?php echo getcwd(); ?></title>
                            %(page_style)s

                </head>


                <body>
                        <h1><?php echo getcwd(); ?></h1>

                        <h2><a name="basic_info">Basic information</a></h2>
                        <div>
                                <!-- Ovdje ce biti info o tom direktoriju -->
                                <object data="basic.info" type="text/plain" width="1000" style="height: 100px">
                                        <a href="basic.info">Your browser does not support this type of text insertion... Sorry! Go to file directly.</a>
                                </object>
                        </div>


                        <h2><a name="plots">Plots</a></h2>
                        <p><form>Filter: <input type="text" name="match" size="30" value="<?php if (isset($_GET['match'])) print htmlspecialchars($_GET['match']);  ?>" /><input type="Submit" value="Search" /></form></p>

                        <div>
                                <?PHP

                                    $displayed = array();
                                    if ($_GET['noplots']) {
                                        print "Plots will not be displayed.\n";
                                    } else {
                                        $other_exts = array('.pdf', '.cxx', '.eps', '.root', '.txt','.C');
                                        $filenames = glob("*.png"); sort($filenames);
                                        foreach ($filenames as $filename) {
                                            if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
                                            array_push($displayed, $filename);
                                            print "<div class='pic'>\n";
                                            print "<h3><a href=\"$filename\">$filename</a></h3>";
                                            print "<a href=\"$filename\"><img src=\"$filename\" style=\"border: none; width: 300px; \"></a>";
                                            $others = array();
                                            foreach ($other_exts as $ex) {
                                                $other_filename = str_replace('.png', $ex, $filename);
                                                if (file_exists($other_filename)) {
                                                    array_push($others, "<a class=\"file\" href=\"$other_filename\">[" . $ex . "]</a>");
                                                    if ($ex != '.txt') array_push($displayed, $other_filename);
                                                }
                                            }
                                            if ($others) print "<p>Also as ".implode(', ',$others)."</p>";
                                            print "</div>";
                                        }
                                    }
                                ?>

                        </div>
                        <div style="display: block; clear:both;">
                                <h2><a name="files">Other files</a></h2>
                                <ul>
                                        <?PHP
                                            foreach (glob("*") as $filename) {
                                                if ($_GET['noplots'] || !in_array($filename, $displayed)) {
                                                    if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
                                                    if (is_dir($filename)) {
                                                        print "<li>[DIR] <a href=\"$filename\">$filename</a></li>";
                                                    } else {
                                                        print "<li><a href=\"$filename\">$filename</a></li>";
                                                    }
                                                }
                                            }
                                        ?>
                                </ul>
                        </div>
                </body>
            </html>
            """ % self.__dict__
