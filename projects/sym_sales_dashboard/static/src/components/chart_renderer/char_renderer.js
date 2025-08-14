/** @odoo-module */

import { registry} from "@web/core/registry"
import { loadJS } from "@web/core/assets"
// import Chart from 'chart.js/auto'
const { Component, onWillStart, useRef, onMounted  } = owl

export class ChartRenderer extends Component {
    setup() {   
        this.ChartRef = useRef("chart")

        onWillStart(async()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
        })

        onMounted(()=>this.renderChart());
    }
    renderChart() {
      new Chart(
        this.ChartRef.el,
        {
          type: this.props.type,
          data: {
            labels: [
              'Red',
              'Blue',
              'Yellow'
            ],
            datasets: [{
              label: 'My First Dataset',
              data: [300, 50, 100],
              
              hoverOffset: 4
            },
            {
              label: 'My second Dataset',
              data: [100, 70, 150],
              hoverOffset: 4
            }]
          },
          options: {
              responsive: true,
              plugins: {
                  legend: {
                      position: 'bottom',
                  },
                  title: {
                      display: true,
                      text: this.props.title
                  }
              }
          }
        }
      );

    }
    
}

ChartRenderer.template = "sym_sales_dashboard.ChartRenderer"
