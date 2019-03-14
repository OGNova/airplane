import React, { Component } from 'react';
import ReactChartkick, {LineChart} from 'react-chartkick';
import Chart from 'chart.js'
import moment from 'moment';
import CountUp from 'react-countup';

import 'react-table/react-table.css'

import Tooltip from './tooltip';
import {globalState} from '../state';

ReactChartkick.addAdapter(Chart)

export default class GuildStats extends Component {
  constructor() {
    super();

    this.state = {
      message: null,
      guild: null,
      mstats: [],
      gstats: {
        totals: {
          messages: 0,
          infractions: 0,
        },
        peaks: {
          messages: {
            user: 'N/A',
            user_count: 0,
          },
          infractions: {
            user: 'N/A',
            user_count: 0,
          },
          emoji: {
            id: '453313514409295873',
            ext: 'gif',
          },
          command: '',
        },
      },
    };
  }

  async statsSetup() {
    try {
      const guild = await globalState.getGuild(this.props.params.gid);
      globalState.currentGuild = guild;
      const config = await guild.getConfig(true);
      this.initialConfig = config.contents;
      const data = await guild.getMessageStats();
      const gstats = await guild.getSelfStats();
      const statsdata = {};

      data.forEach((elem) => {
        statsdata[moment(elem.day).format('llll')] = elem.count;
      });
      this.setState({
        guild: guild,
        mstats: statsdata,
        gstats: gstats,
      });
    } catch (e){
      console.error(`Error retrieving guild stats data: ${e}`);
    }
  }

  componentWillMount() {
    this.statsSetup();
  }

  componentWillUnmount() {
    globalState.currentGuild = null;
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
    const messageUser = this.state.gstats.peaks.messages.user.username
      ? (<Tooltip position='left' text={this.state.gstats.peaks.messages.user.id} trigger={
          <span>{this.state.gstats.peaks.messages.user.username}<span className="darker pad-right">#{this.state.gstats.peaks.messages.user.discrim.padStart(4, "0")}</span></span>
        } />)
      : this.state.gstats.peaks.messages.user;
    const infractionUser = this.state.gstats.peaks.infractions.user.username
      ? (<Tooltip position='left' text={this.state.gstats.peaks.infractions.user.id} trigger={
          <span>{this.state.gstats.peaks.infractions.user.username}<span className="darker pad-right">#{this.state.gstats.peaks.infractions.user.discrim.padStart(4, "0")}</span></span>        } />)
      : this.state.gstats.peaks.infractions.user;

    return (<div>
      {this.state.message && <div className={"alert alert-" + this.state.message.type}>{this.state.message.contents}</div>}
      <div className="row config-row">
        <div className="col-lg-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <i className="fas fa-chart-line"></i> Guild Weekly Message Throughput
            </div>
            <div className="panel-body">
              <LineChart data={this.state.mstats} />
              </div>
            </div>
            <div className="panel panel-default">
              <div className="panel-heading"><i className="fas fa-info-circle"></i> Guild Info</div>
              <div className="panel-body">
                <table className="table">
                  <thead>
                    <tr>
                      <td><h4>Stat</h4></td>
                      <td><h4>Value</h4></td>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Total Guild Messages</td>
                      <td><CountUp separator="," start={0} end={this.state.gstats.totals.messages} useGrouping={true} duration={2} redraw={true} /></td>
                    </tr>
                    <tr>
                      <td>Total Guild Infractions</td>
                      <td><CountUp separator="," start={0} end={this.state.gstats.totals.infractions} useGrouping={true} duration={2} redraw={true} /></td>
                    </tr>
                    <tr>
                      <td>User who has sent the most messages</td>
                      <td>{messageUser}</td>
                    </tr>
                    <tr>
                      <td># Messages</td>
                      <td><CountUp separator="," start={0} end={this.state.gstats.peaks.messages.user_count} useGrouping={true} duration={2} redraw={true} /></td>
                    </tr>
                    <tr>
                      <td>User with most infractions</td>
                      <td>{infractionUser}</td>
                    </tr>
                    <tr>
                      <td># Infractions</td>
                      <td>{this.state.gstats.peaks.infractions.user_count}</td>
                    </tr>
                    <tr>
                      <td>Most Used Emoji</td>
                      <td>
                        <Tooltip position='left' text={this.state.gstats.peaks.emoji.id} trigger={
                          <img height="32px" src={`https://cdn.discordapp.com/emojis/${this.state.gstats.peaks.emoji.id}.${this.state.gstats.peaks.emoji.ext}`}/>
                        } />
                      </td>
                    </tr>
                    <tr>
                      <td>Most Used Command</td>
                      <td>{this.state.gstats.peaks.command}</td>
                    </tr>
                  </tbody>
                </table>

              </div>
            </div>
          </div>
        </div>
    </div>);
  }
}
