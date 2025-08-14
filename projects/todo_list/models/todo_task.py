from odoo import models, fields

class TodoTask(models.Model):
    _name = "todo.task"
    _description = "To-Do Task"

    name = fields.Char("Task Name", required=True)
    completed = fields.Boolean("Completed", default=False)
    category_id = fields.Many2one("todo.category", string="Category")
    tag_ids = fields.Many2many("todo.tag", string="Tags")


class TodoCategory(models.Model):
    _name = "todo.category"
    _description = "Task Category"

    name = fields.Char("Category Name", required=True)
    

class TodoTag(models.Model):
    _name = "todo.tag"
    _description = "Task Tag"

    name = fields.Char("Tag Name", required=True)
