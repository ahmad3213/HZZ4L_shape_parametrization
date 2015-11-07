from Logger import *
import os, time

class FolderGuard(object):
    """
    Watch Folder for changes
    - time interval watch
    - container of snapshots
        - diffs between snapshots
        
    TODO: Add functionality for updated files, not only new ones
    """
    def __init__(self, path_to_watch="."):

        self.log = Logger().getLogger(self.__class__.__name__, 10)
        self.path_to_watch = path_to_watch
        self.stop = False
        self.snapshots = dict()  # list/dict of snapshots of the folder
        
    def watch(self, path=None, time_interval = 10):
        """
        Watch a path in fixed time intervals and print out the changes
        """
        
        if path:
            self.path_to_watch = path
        #before = dict ([(f, None) for f in os.listdir (path_to_watch)])
        self.log.info('Watching folder: {0}'.format(self.path_to_watch))
        before = self._list_dir()
        while 1:
            time.sleep (time_interval)
            #after = dict ([(f, None) for f in os.listdir (path_to_watch)])
            after = self._list_dir()
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
            if added: 
                print "Added: ", ", ".join (added)
            if removed: 
                print "Removed: ", ", ".join (removed)
            before = after            
            if self.stop: break
            
            
    def _list_dir(self, path=None, filter = "*"):
        if path:
            self.path_to_watch = path
        return dict([(f, None) for f in os.listdir (self.path_to_watch)])
            
    def take_snapshot(self, path=None):
        """
        Take folder state snapshot and put in dict() of format {"path":[list of snapshots]}
        """
        
        if path:
            self.path_to_watch = path
        try:
            self.snapshots[self.path_to_watch]
        except KeyError:
            self.snapshots[self.path_to_watch] = [self._list_dir()]
            self.log.info('Taking snapshot 1 in folder: {0}'.format(self.path_to_watch))
        else:
            self.snapshots[self.path_to_watch].append(self._list_dir())
            self.log.info('Taking snapshot {1} in folder: {0}'.format(self.path_to_watch, len(self.snapshots[self.path_to_watch])+1))
        return
        
        
    def get_snapshots_list(self, path=None):
        """
        Get list of snapshots for given path
        """
        if path:
            self.path_to_watch = path
        try:
            self.snapshots[self.path_to_watch]
        except KeyError,
            raise KeyError, 'No snapshot has been taken for path: {0}'.format(self.path_to_watch)
        else:
           return self.snapshots[self.path_to_watch]
           
    def get_diff(self, path=None, snapshots = (0,-1)):
        """
        Gives the diff between two snapshots
        - by default the diff is between first and the last snapshot
        """
        pass
            
            
            
            
        
       
        