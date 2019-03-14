import React, { Component } from 'react';
import CountUp from 'react-countup';

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
          <i className="fas fa-server"></i> Guilds
        </div>
        <div className="panel-body">
          <GuildsTable guilds={this.state.guilds}/>
        </div>
      </div>
    );
  }
}

// class ControlPanel extends Component {
//   constructor() {
//     super();

//     this.messageTimer = null;

//     this.state = {
//       guilds: null,
//       message: null,
//     };
//   }

//   componentWillMount() {
//     globalState.getCurrentUser().then((user) => {
//       user.getGuilds().then((guilds) => {
//         this.setState({guilds});
//       });
//     });
//   }

//   onDeploy() {
//     globalState.deploy().then(() => {
//       this.renderMessage('success', 'Deploy Started');
//     }).catch((err) => {
//       this.renderMessage('danger', `Deploy Failed: ${err}`);
//     });
//   }

//   renderMessage(type, contents) {
//     this.setState({
//       message: {
//         type: type,
//         contents: contents,
//       }
//     })

//     if (this.messageTimer) clearTimeout(this.messageTimer);

//     this.messageTimer = setTimeout(() => {
//       this.setState({
//         message: null,
//       });
//       this.messageTimer = null;
//     }, 5000);
//   }

//   render() {
//     return (
//       <div className="panel panel-default">
//         {this.state.message && <div className={"alert alert-" + this.state.message.type}>{this.state.message.contents}</div>}
//         <div className="panel-heading">
//           <i className="fas fa-cogs"></i> Control Panel
//         </div>
//         <div className="panel-body">
//         <a href="#" onClick={() => this.onDeploy()} className="btn btn-success btn-block">Deploy</a>
//         </div>
//       </div>
//     );
//   }
// }

class StatsPanel extends Component {
  render () {
    const panelClass = `panel panel-${this.props.color}`;
    const iconClass = `${this.props.icon} fa-5x`;

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
                  <CountUp className={this.props.text.toLowerCase()} separator="," start={0} end={this.props.data || 0} useGrouping={true} duration={2} redraw={true} />
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

    const statsPanels = [];
    statsPanels.push(
      <StatsPanel color='primary' icon='fas fa-comment-alt' data={this.state.stats.messages || 0} text='Messages' key='messages' />
    );
    statsPanels.push(
      <StatsPanel color='green' icon='fab fa-discord' data={this.state.stats.guilds || 0} text='Guilds' key='guilds' />
    );
    statsPanels.push(
      <StatsPanel color='yellow' icon='fas fa-users' data={this.state.stats.users || 0} text='Members' key='members' />
    );
    statsPanels.push(
      <StatsPanel color='red' icon='fas fa-hashtag' data={this.state.stats.channels || 0} text='Channels' key='channels' />
    );

    return (
      <div className='top-stats'>
        {statsPanels}
      </div>
    );
  }
}

class Dashboard extends Component {
  render() {
    let parts = [];

    parts.push(
      <div className="row config-row" key='statsrow'>
        <Stats />
      </div>
    );

    parts.push(
      <center>
        <div>
        {/* <div className="row dashguild" key='dashguildlist'> */}
          <div className="col-lg-8">
            <DashboardGuildsList />
          </div>
        </div>
      </center>
    );

		return (
      <div className="config-row">
        {parts}
      </div>
    );
  }
}
export default Dashboard;
