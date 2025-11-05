/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formatFloatTime } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const { Component, useState, onWillUpdateProps, onWillStart, onWillDestroy } = owl;

export class AcsTimer extends Component {
    setup() {
        super.setup();
        this.state = useState({
            duration:
                this.props.duration !== undefined
                    ? this.props.duration
                    : this.props.record.data[this.props.duration_field],
        });

        const newLocal = this;
        let timer_running;
        timer_running = 0;
        if (this.props.record.data[this.props.acs_timer_start_field]){
            timer_running = 1;
        }
        if (this.props.record.data[this.props.acs_timer_start_field] && this.props.record.data[this.props.acs_timer_stop_field]){
            timer_running = 0;
        }
        
        this.ongoing =
            this.props.ongoing !== undefined
                ? newLocal.props.ongoing
                : timer_running;

        onWillStart(() => this._runTimer());
        onWillUpdateProps((nextProps) => {
            this.ongoing = nextProps.ongoing;
            this._runTimer();
        });
        onWillDestroy(() => clearTimeout(this.timer));
    }

    get duration() {
        // formatFloatTime except 1,5 =  1h30min but in this case 1,5 = 1min30
        return formatFloatTime(this.state.duration / 60, { displaySeconds: true });
    }

    _runTimer() {
        if (this.ongoing) {
            this.timer = setTimeout(() => {
                this.state.duration += 1 / 60;
                this._runTimer();
            }, 1000);
        }
    }
}

AcsTimer.supportedTypes = ["float"];
AcsTimer.template = "web_timer_widget.AcsTimeCounter";

AcsTimer.props = {
    ...standardFieldProps,
    acs_timer_start_field: String,
    acs_timer_stop_field: String,
    duration_field: String,
};

AcsTimer.extractProps = ({ attrs }) => {
    return {
        acs_timer_start_field: attrs.options.widget_start_field,
        acs_timer_stop_field: attrs.options.widget_stop_field,
        duration_field: attrs.options.duration_field,
    };
};

registry.category("fields").add("AcsTimer", AcsTimer);
