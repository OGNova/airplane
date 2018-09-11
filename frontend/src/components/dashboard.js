import React, { Component } from 'react';

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

class Dashboard extends Component {
  render() {
		return (
      <div>
        <PageHeader name="Dashboard" />
        <div class="row">
        <div class="col-lg-3 col-md-6">
        <div class="panel panel-primary">
          <div class="panel-heading">
            <div class="row">
              <div class="col-xs-3">
                <i class="fa fa-comments fa-5x"></i>
              </div>
              <div class="col-xs-9 text-right">
                <div class="huge"><CountUp className={"messages"} separator={","} start={0} end={this.state.stats.messages} useGrouping={true} duration={3} redraw={true} /></div>
                <div>Total Sent Messages</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6">
        <div class="panel panel-green">
          <div class="panel-heading">
            <div class="row">
            <div class="col-xs-3">
                <i class="fa fa-server fa-5x"></i>
              </div>
              <div class="col-xs-9 text-right">
                <div class="huge"><CountUp className={"guilds"} separator={","} start={0} end={this.state.stats.guilds} useGrouping={true} duration={3} redraw={true} /></div>
                <div>Total Guilds Initialized</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6">
        <div class="panel panel-yellow">
          <div class="panel-heading">
            <div class="row">
              <div class="col-xs-3">
                <i class="fa fa-user fa-5x"></i>
              </div>
              <div class="col-xs-9 text-right">
                <div class="huge"><CountUp className={"users"} separator={","} start={0} end={this.state.stats.users} useGrouping={true} duration={3} redraw={true} /></div>
                <div>Registered Users</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6">
        <div class="panel panel-red">
          <div class="panel-heading">
            <div class="row">
              <div class="col-xs-3">
                <i class="fa fa-hashtag fa-5x"></i>
              </div>
              <div class="col-xs-9 text-right">
                <div class="huge"><CountUp className={"channels"} separator={","} start={0} end={this.state.stats.channels} useGrouping={true} duration={3} redraw={true} /></div>
                <div>Total Channels</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
      <div className="row">
        <div className="col-lg-12">
          <DashboardGuildsList />
        </div>
        </div>
		</div>
    );
  }
}

export default Dashboard;
