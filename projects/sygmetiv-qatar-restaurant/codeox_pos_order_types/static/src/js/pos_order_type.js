import { registry } from "@web/core/registry";
import { Base } from "@point_of_sale/app/models/related_models";


export class PosOrderType extends Base {
    static pythonModel = "pos.order.type";
}

registry.category("pos_available_models").add(PosOrderType.pythonModel, PosOrderType);