import React, { Component } from 'react';

import { Tooltip } from 'react-tippy';

export default class lTooltip extends Component {
  render() {
    const popperOptions = {
      positionFixed: true,
    }
    // <div data-toggle='tooltip' data-placement={position} title={this.props.text} data-container='body' className='d-inline'>{this.props.trigger}</div>
    return (
      <Tooltip
        title={this.props.text}
        position={this.props.position || 'right'}
        arrow={true}
        popperOptions={popperOptions}
        interactive={typeof this.props.interactive === 'undefined' ? true : this.props.interactive}
        distance={this.props.distance || 20}
        size="big"
        >
          {this.props.trigger}
      </Tooltip>
    );
  }
}
