/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { htmlToCanvas } from "@point_of_sale/app/printer/render_service";
import { rpc } from "@web/core/network/rpc";

patch(BasePrinter.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async printReceipt(receipt, configId=null) {
        if (receipt) {
            console.log(receipt.outerHTML);
            this.receiptQueue.push(receipt);
        }
        let image, printResult;
        while (this.receiptQueue.length > 0) {
            receipt = this.receiptQueue.shift();
            const htmlData = await rpc("/pos/parse_data",{
                    data: receipt.outerHTML,
                });
            const kot_data = await rpc("/pos/flask_url",{
                config_id: configId
            });
            const flask_url = kot_data.url
            const printerName = this.config.name
            try {
                printResult = await fetch('http://localhost:5000/print', {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({content: htmlData.data, printer: printerName})
                });
            } catch {
                try {
                    printResult = await fetch(flask_url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({content: htmlData.data, printer: printerName})
                    });
                }
                catch {
                    // Error in communicating to the IoT box.
                    this.receiptQueue.length = 0;
                    return this.getActionError();
                }
            }
            // rpc call is okay but printing failed because
            // IoT box can't find a printer.
            if (!printResult || printResult.result === false) {
                this.receiptQueue.length = 0;
                return this.getResultsError(printResult);
            }
        }
        return { successful: true };
    }
})