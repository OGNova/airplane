import React, { Component } from 'react';

export default class SavePrompt extends Component {
  constructor(props) {
    super(props);
    this.state = {
      show: '',
    };
  }

  static getDerivedStateFromProps (props) {
    // console.log(props.showCondition);
    return {
      show: props.showCondition ? 'show' : '',
    };
  }

  render() {
    // console.log(`from state: ${this.state.show}`);
    return (
      <div className={`panel-footer snackbar ${this.state.show}`}>
        <div className="pull-left message">{this.props.warningText || 'Careful — you have unsaved changes!'}</div>
        <div className="pull-right">
          <button
            onClick={(e) => this.props.onReset(e)}
            type="button"
            className="btn btn-outline btn-text btn-prompt ">
            {this.props.resetText || 'Reset'}
          </button>

          <button
            onClick={(e) => this.props.onSave(e)}
            type="button"
            className="btn btn-success btn-prompt">
            {this.props.saveText || 'Save Changes'}
          </button>
        </div>
      </div>
    );
  }
}
