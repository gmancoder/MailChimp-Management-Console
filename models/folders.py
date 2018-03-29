#!/usr/bin/env python
from models.shared import db
from sqlalchemy.orm.collections import attribute_mapped_collection
import datetime

class Folder(db.Model):
    __tablename__ = "folder"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    mailchimp_id = db.Column(db.String(10), nullable=True)
    name = db.Column(db.String(200))
    folder_type = db.Column(db.String(200))
    children = db.relationship('Folder', 
    	cascade="all", 
    	backref=db.backref("parent", remote_side="Folder.id"))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))


    def __init__(self, name, parent=None):
        self.name = name
        self.parent_folder_id = parent
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

    def append(self, nodename):
        self.children[nodename] = TreeNode(nodename, parent=self)

    def __repr__(self):
        return "TreeNode(name=%r, id=%r, parent_id=%r)" % (
                    self.name,
                    self.id,
                    self.parent_id
                )
    def drawBreadCrumb(self, breadcrumb, lvl=0):
        if lvl < 0:
            breadcrumb = '<li><a href="/folder/%s">%s</a></li>\n%s' % (self.id, self.name, breadcrumb)
        else:
            breadcrumb = '<li><strong>%s</strong></li>\n%s' % (self.name, breadcrumb)
        if self.parent != None:
            return self.parent.drawBreadCrumb(breadcrumb, lvl - 1)
        return breadcrumb

    def drawFolderTree(self, current_folder, cls="js-folder-context"):
        a_classes = ""
        li_classes = ""
        tree = ""
        try:
            if self.id == current_folder.id:
                li_classes += " jstree-open "
                a_classes = " jstree-clicked "
            elif self.child_is_current(current_folder):
                li_classes += " jstree-open "

            tree = "<li class='%s %s' id='%s' title='%s'><a class='%s' href='/folder/%s'>%s</a>" % (cls, li_classes, self.id, self.name, a_classes, self.id, self.name)
            if self.children:
                tree = '%s\n<ul>' % tree
                for child in self.children:
                    tree = '%s\n%s' % (tree, child.drawFolderTree(current_folder, cls))
                tree = '%s</ul>\n' % tree
            tree = '%s</li>' % tree
        except:
            pass
        return tree
    def child_is_current(self, current_folder):
        for child in self.children:
            if child.id == current_folder.id:
                return True
            elif child.children:
                return child.child_is_current(current_folder)
        return False

