/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";


patch(PosStore.prototype, {
    async closeSession() {
        if (!this.config.allow_closing_session) {
            return this.notification.add(_t('You have not Permission close session'), 3000);
        }
        return await super.closeSession();
    }

})