import React, { Component } from 'react';
import {diff as DiffEditor} from 'react-ace';
import moment from 'moment';

import {globalState} from '../state';
import SavePrompt from './save_prompt';

import 'brace/mode/yaml'
import 'brace/theme/monokai'

const defaultValue = [``,``]

export default class GuildConfigHistory extends Component {
  constructor() {
    super();

    this.messageTimer = null;
    this.initialConfig = null;

    this.state = {
      message: null,
      guild: null,
      value: defaultValue,
      readonly: false,
      history: [],
      mode: 'yaml',
      theme: 'monokai',
    };

    this.setConfigSelected = this.setConfigSelected.bind(this);
  }

  async configSetups() {
    let guild = {};
    try {
      guild = await globalState.getGuild(this.props.params.gid);
    } catch (err) {
      console.error(`Failed to find guild (${this.props.params.gid}) for config edit: ${err.message}`);
      guild = undefined;
    }
    if(!guild) return;

    try {
      globalState.currentGuild = guild;
      const config = await guild.getConfig(true);
      this.initialConfig = config.contents;
      const data = await guild.getConfigHistory();
      this.setState({
        guild: guild,
        value: [
          data[0].after,
          this.initialConfig
        ],
        history: data,
        readonly: true,
      });
    } catch (err) {
      console.error(`Error getConfigHistory: ${err.message}`);
      this.renderMessage('danger', 'Failed to fetch config history');
    }
  }

  componentWillMount() {
    this.configSetups();
  }

  componentWillUnmount() {
    globalState.currentGuild = null;
  }

  onSave() {
    this.state.guild.putConfig(this.state.value[1])
      .then(() => {
        this.initialConfig = this.state.value[0];
        this.renderMessage('success', 'Restored Configuration!');
        globalState.currentGuild.getConfigHistory().then((data) => {
          this.setState({value: [data[0].after, data[0].after], history: data})
        });
      })
      .catch((err) => {
        this.renderMessage('danger', `Failed to restore configuration: ${err}`);
      });
  }

  onReset() {
    this.state.contents = this.initialConfig;
    this.setState({
      hasUnsavedChanges: false,
    });
  }

  renderMessage(type, contents) {
    this.setState({
      message: {
        type: type,
        contents: contents,
      }
    })

    if (this.messageTimer) clearTimeout(this.messageTimer);

    this.messageTimer = setTimeout(() => {
      this.setState({
        message: null,
      });
      this.messageTimer = null;
    }, 5000);
  }

  setConfigSelected(e) {
    const index = e.value;
    this.setState({
      value: [
        this.state.history[0].after,
        this.state.history[index].after
      ]
    });
  }

  render() {
      const newLocal = this.state.history;
    const options = newLocal
      .map((currentValue, index) => {
        return {
          value: index,
          createdAt: new Date(currentValue.created).toLocaleString(),
          author: `${currentValue.user.username}#${String(currentValue.user.discriminator).padStart(4, "0")}`,
          createdTS: currentValue.created_timestamp,
        }
      });

    let buttonsList = []

    // Thanks, Tiemen
    if (this.state.history) {
      options.forEach((change) => {
        buttonsList.push(
          <a key={change.createdTS} onClick={() => {this.setConfigSelected({value: change.value})}} className="list-group-item">
            <i className="fa fa-history fa-fw"></i> {change.author}
            <span className="pull-right text-muted small" title={change.createdAt}>
              <em>{moment(new Date(change.createdTS*1000).toLocaleString()).fromNow()}</em>
            </span>
          </a>
        );
      });
    }

    return (<div>
      {this.state.message && <div className={"alert alert-" + this.state.message.type}>{this.state.message.contents}</div>}
      <div className="row config-row">
        <div className="col-lg-9">
          <div className="panel panel-default">
            <div className="panel-heading">
              <i className="fas fa-history"></i> Config History Viewer
            </div>
            <div className="panel-body">
              <DiffEditor
                mode={this.state.mode}
                theme={this.state.theme}
                value={this.state.value}
                width="100%"
                readOnly={this.state.readonly}
              />
            </div>

            <SavePrompt showCondition={this.state.hasUnsavedChanges &&  this.state.guild && this.state.guild.role != 'viewer'
              && this.state.guild.role != 'editor'} onSave={() => {this.onSave()}}  onReset={() => {this.onReset()}} />

          </div>
        </div>
        <div className="col-lg-3">
          <div className="panel panel-default panel-short">
            <div className="panel-heading">
              <i className="fa fa-history fa-fw"></i> History
            </div>
            <div className="panel-body">
              <div className="list-group">
                <a key='config' className="list-group-item">
                  <i className="fa fa-edit fa-fw"></i> Current Version
                </a>
                {buttonsList}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>);
  }
}
