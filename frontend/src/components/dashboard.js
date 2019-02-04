import React, { Component } from 'react';
import CountUp from 'react-countup';

import PageHeader from './page_header';
import GuildsTable from './guilds_table';
import {globalState} from '../state';

class DashboardGuildsList extends Component {
  constructor() {
    super();
    this.state = {guilds: null};
  }

  componentWillMount() {
    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });
  }

  render() {
    return (
      <div className="panel panel-default">
        <div className="panel-heading">
          Guilds
        </div>
        <div className="panel-body">
          <GuildsTable guilds={this.state.guilds}/>
        </div>
      </div>
    );
  }
}

class ControlPanel extends Component {
  constructor() {
    super();

    this.messageTimer = null;

    this.state = {
      guilds: null,
      message: null,
    };
  }

  componentWillMount() {
    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });
  }

  onDeploy() {
    globalState.deploy().then(() => {
      this.renderMessage('success', 'Deploy Started');
    }).catch((err) => {
      this.renderMessage('danger', `Deploy Failed: ${err}`);
    });
  }

  onBotRestart() {
    globalState.restartBot().then(() => {
      this.renderMessage('success', 'Restarting Bot');
    }).catch((err) => {
      this.renderMessage('danger', `Restart Failed: ${err}`);
    });
  }
    
  onBotShutdown() {
    globalState.shutdownBot().then(() => {
      this.renderMessage('success', 'Shutting Bot Down');
    }).catch((err) => {
      this.renderMessage('danger', `Shutdown Failed: ${err}`);
    });
  }

  onFrontendRestart() {
    globalState.restartFrontend().then(() => {
      this.renderMessage('success', 'Restarting Frontend');
    }).catch((err) => {
      this.renderMessage('danger', `Restart Failed: ${err}`)
    })
  }

  onFrontendShutdown() {
    globalState.shutdownFrontend().then(() => {
      this.renderMessage('success', 'Shutting Frontend Down');
    }).catch((err) => {
      this.renderMessage('danger', `Shutdown Failed: ${err}`)
    })
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

  render() {
    return (
      <div className="panel panel-default">
        {this.state.message && <div className={"alert alert-" + this.state.message.type}>{this.state.message.contents}</div>}
        <div className="panel-heading">
          <i className="fa fa-cog fa-fw"></i> Control Panel
        </div>
        <div className="panel-body">
        <a href="#" onClick={() => this.onDeploy()} className="btn btn-success btn-block">Deploy</a>
        <a href="#" onClick={() => this.onBotRestart()} className="btn btn-warning btn-block">Restart Bot</a>
        <a href="#" onClick={() => this.onBotShutdown()} className="btn btn-danger btn-block">Shutdown Bot</a>
        <a href="https://aetherya.stream" onClick={() => this.onFrontendRestart()} className="btn btn-warning btn-block">Restart Frontend</a>
        <a href="https://aetherya.stream" onClick={() => this.onFrontendShutdown()} className="btn btn-danger btn-block">Shutdown Frontend</a>
        </div>
      </div>
    );
  }
}

class StatsPanel extends Component {
  render () {
    const panelClass = `panel panel-${this.props.color}`;
    const iconClass = `fa fa-${this.props.icon} fa-5x`;

    return (
      <div className="col-lg-3 col-md-6">
        <div className={panelClass}>
          <div className="panel-heading">
            <div className="row">
              <div className="col-xs-3">
                <i className={iconClass}></i>
              </div>
              <div className="col-xs-9 text-right">
                <div className="large">
                  <CountUp className={this.props.text.toLowerCase()} separator="," start={0} end={this.props.data || 0} useGrouping={true} duration={3} redraw={true} />
                </div>
                <div>{this.props.text}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

class Stats extends Component {
  constructor() {
    super();
    this.state = {
      stats: {
        messages: null,
        guilds: null,
        users: null,
        channels: null
      }
    };
  }

  render() {
    if (this.state.stats.guilds === null) {
      globalState.getStats().then((stats) => {
        this.setState({stats});
      });
    }

    let statsPanels = [];
    statsPanels.push(
        <StatsPanel color='primary' icon='comments' data={this.state.stats.messages || 0} text='Messages' key='messages' />
    );
    statsPanels.push(
        <StatsPanel color='green' icon='server' data={this.state.stats.guilds || 0} text='Guilds' key='guilds' />
    );
    statsPanels.push(
        <StatsPanel color='yellow' icon='user' data={this.state.stats.users || 0} text='Users' key='users' />
    );
    statsPanels.push(
        <StatsPanel color='red' icon='hashtag' data={this.state.stats.channels || 0} text='Channels' key='channels' />
    );

    return (
      <div>
        {statsPanels}
      </div>
    );
  }
}

class Dashboard extends Component {
  render() {
    let parts = [];

    parts.push(
      <PageHeader name="Dashboard" />
    );

    parts.push(
      <div className="row">
        <Stats />
      </div>
    );

    parts.push(
      <div className="row">
        <div className="col-lg-8">
          <DashboardGuildsList />
        </div>
        {
          globalState.user && globalState.user.admin &&
          <div className="col-lg-4"> 
            <ControlPanel />
          </div>
        }
      </div>
    );

		return (
      <div>
        {parts}
      </div>
    );
  }
}

export default Dashboard;
