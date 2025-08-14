/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component, useState,onWillStart,useRef } = owl;
import { useService } from "@web/core/utils/hooks";


export class OwlTodoList extends Component{
    setup(){
        this.state = useState({ 
            task:{name:"", completed:false,categories:[]},
            taskList:[],
            categories:[],
            tags:[],
            isEdit: false,
            activeId: false,
        });

        this.orm = useService("orm")
        this.model="todo.task"
        onWillStart(async()=>{
            this.GetAlTasks()
        })
    }

    async GetAlTasks(){
        this.state.taskList = await this.orm.searchRead(this.model,[],["id","name","completed","category_id"])
        if (!this.state.categories.length) {
            await this.GetallCategories();
        }
    
        this.state.taskList = this.state.taskList.map(task => {
            const category = this.state.categories.find(c => c.id === task.category_id);
            return { ...task, category_name: category ? category.name : "Uncategorized" };
        });

    }

    async GetallCategories(){
        this.state.categories = await this.orm.searchRead("todo.category",[],["id","name"])
    }

    async addTask(){
        this.resetForm()
        this.state.activeId = false
        this.state.isEdit = false
    }

    async EditTask(task){
        this.state.activeId = task.id
        this.state.isEdit = true
        this.state.task = {...task}

    }

   async SaveTask() {
    console.log("Saving Task:", this.state.task);
    console.log("Edit Mode:", this.state.isEdit, "Active ID:", this.state.activeId);

    if (!this.state.isEdit) {
        try {
            await this.orm.create(this.model, [{
                name: this.state.task.name,
                completed: this.state.task.completed,
                category_id: this.state.task.category_id || false, // Ensure valid field
            }]);
        } catch (error) {
            console.error("Error creating task:", error);
        }
    } else {
        if (!this.state.activeId) {
            console.error("Error: No active ID found for editing!");
            return;
        }

        try {
            const result = await this.orm.write(this.model, [this.state.activeId], {
                name: this.state.task.name,
                completed: this.state.task.completed,
                category_id: this.state.task.category_id || false, // Ensure valid ID
            });

            console.log("Write Result:", result);
        } catch (error) {
            console.error("Error updating task:", error);
        }
    }
    
    await this.GetAlTasks();
}

    async resetForm(){
        this.state.task =await {name:"", completed:false}
    }

    async deleteTask(task){
        await this.orm.unlink(this.model,[task.id])
        await this.GetAlTasks()

    }

    async addcategory() {
        this.resetForm();
        this.state.activeId = false;
        this.state.isEdit = false;
    }

    async SaveCategory() {
        if (!this.state.newCategoryName.trim()) {
            return;
        }
    
        try {
            const newCategory = await this.orm.create("todo.category", [{ name: this.state.newCategoryName }]);
    
            await this.GetallCategories();
    
            this.state.newCategoryName = "";
    
            document.getElementById("categoryModal").querySelector(".btn-close").click();
        } 
        catch (error) {
            console.error("Error saving category:", error);
        }
    }
    
}
OwlTodoList.template = "owl.TodoList";

registry.category("actions").add("owl.action_todo_list_js", OwlTodoList);





