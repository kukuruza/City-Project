# TreeNode - class for operations on trees
#   To read a tree from json, each element of json must be of the form:
#   element = {'name'     : 'myname', 
#              'known'    : false/true, 
#              'children' : [ <array or empty> ] }
#
#   The best match to a query element in the tree is defined as 
#   the closest to the query 'known' element (traversing up the tree)
#

from __future__ import print_function
import logging


class TermTree(dict):
    def __init__(self, name, known=False, children=None):
        self.__dict__ = self
        self.name = str(name)
        self.known = known
        self.children = [] if not children else children

    def printout (self, indent = None):
        print (' ' * (indent or 0), self.name, '*' if self.known else '')
        for child in self.children:
            child.printout ((indent or 0) + 2)

    @staticmethod
    def from_dict(dict_):
        """ Recursively (re)construct TreeNode-based tree from dictionary. """
        root = TermTree(dict_['name'], dict_['known'], dict_['children'])
        root.children = list(map(TermTree.from_dict, root.children))
        return root

    def check_uniqueness (self, pool = []):
        ''' check if elements of tree are unique '''
        ishead = False if pool else True
        pool.append (self.name)
        for child in self.children:
            pool = child.check_uniqueness (pool)
        return len(pool) == len(set(pool)) if ishead else pool

    def best_match (self, query, ishead=True):
        ''' find the best match for a query '''
        match = None
        found_known = False
        if self.name == query:
            # found the query
            match = query
        else:
            # we need to go deeper
            for child in self.children:
                match, found_known = child.best_match (query, ishead=False)
                if match:
                    break
        # at this point we either found a match or not.
        # if found, we know whether it is found_known in CHILDREN or not
        if match and not found_known and self.known:
            match = self.name
            found_known = True
        # at this point we either found a match or not and found_known here
        if ishead:
            # a user only sees match or None
            return match if match and found_known else self.name
        else:
            return match, found_known

    def _get_path_to_node_ (self, query):
        ''' returns the full path from the root of the tree to the  '''
        match = None
        if self.name == query:
            # found the query
            return [self.name]
        else:
            # we need to go deeper
            for child in self.children:
                path_to_node = child._get_path_to_node_ (query)
                if path_to_node is not None:
                    # some child returned a valid path
                    return [self.name] + path_to_node
        # at this point the match is abscent
        return None

    def get_common_root (self, query1, query2):
        ''' get the deepest common element between two queries '''
        # get path from the root for both queries
        logging.debug ('finding common root between %s and %s' % (query1, query2))
        path1 = self._get_path_to_node_(query1)
        path2 = self._get_path_to_node_(query2)
        if path1 is None or path2 is None:
            raise Exception ('"%s" or "%s" is not in the tree' % (query1, query2))

        # go through this path and find where it diverges
        assert len(path1) >= 1 and len(path2) >= 1 and path1[0] == path2[0]
        for i in range (max(len(path1), len(path2))):
            if len(path1) <= i or len(path2) <= i or path1[i] != path2[i]:
                logging.debug ('found common root = %s' % common_root)
                return common_root
            common_root = path1[i]


if __name__ == '__main__':
    ''' Demo '''
    import json

    tree = TermTree('Parent')
    tree.children.append(TermTree('Child 1'))
    child2 = TermTree('Child 2')
    tree.children.append(child2)
    child2.children.append(TermTree('Grand Kid'))
    child2.children[0].children.append(TermTree('Great Grand Kid'))
    tree.printout()
    print()

    tree2 = TermTree.from_dict(json.load(open('dictionary.json')))
    tree2.printout()
    print (tree2.check_uniqueness())
    print (tree2.best_match('object'))


