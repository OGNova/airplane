import React, { Component } from 'react';
import debounce from 'lodash/debounce';
import {globalState, debug} from '../state';
import ReactTable from 'react-table';
import Tooltip from './tooltip'

class Affirmative extends Component {
  render () {
    return (
      <Tooltip position='left' text='Active' trigger={<i className="fas fa-check-circle" style={{color: 'green'}}></i>} />
    );
  }
}

class Denial extends Component {
  render () {
    return (
      <Tooltip position='left' text='Inactive' trigger={<i className="fas fa-times-circle" style={{color: 'red'}}></i>} />
    );
  }
}

class Infraction extends Component {
    render () {
        let inner;
        switch (this.props.type){
            case 'tempban':
            case 'ban':
                inner = (<i className="fas fa-gavel"></i>);
                break;
            case 'warning':
                inner = (<i className="fas fa-exclamation"></i>);
                break;
            case 'mute':
            case 'tempmute':
                inner = (<i className="fas fa-microphone-slash"></i>);
                break;
            case 'unban':
                inner = (<i className="fas fa-unlock-alt"></i>);
                break;
            case 'kick':
                inner = (<i className="fas fa-door-open"></i>);
                break;
            case 'note':
                inner = (<i className="fas fa-sticky-note"></i>);
                break;
            default:
                inner = (<i className="fas fa-question"></i>);
                break;
        }
        return (<Tooltip position='right' text={this.props.type} trigger={inner} />);
    }
}

class InfractionTable extends Component {
  render() {
    const inf = this.props.infraction;

    return (
      <table className="table table-hover">
        <thead>
          <tr>
            <th className="col-xs-2"></th>
            <th className="col-xs-10"></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>ID</td>
            <td>{inf.id}</td>
          </tr>
          <tr>
            <td>Target User</td>
            <td>{inf.user.username}#{String(inf.user.discriminator).padStart(4, "0")} ({inf.user.id})</td>
          </tr>
          <tr>
            <td>Actor User</td>
            <td>{inf.actor.username}#{String(inf.actor.discriminator).padStart(4, "0")} ({inf.actor.id})</td>
          </tr>
          <tr>
            <td>Created At</td>
            <td>{inf.created_at ? new Date(inf.created_at).toLocaleString() : inf.created_at}</td>
          </tr>
          <tr>
            <td>Expires At</td>
            <td>{inf.expires_at ? new Date(inf.expires_at).toLocaleString() : inf.expires_at}</td>
          </tr>
          <tr>
            <td>Type</td>
            <td>{inf.type.name}</td>
          </tr>
          <tr>
            <td>Reason</td>
            <td>{inf.reason}</td>
          </tr>
        </tbody>
      </table>
    );
  }
}

class GuildInfractionInfo extends Component {
  render() {
    return (
      <div className="panel panel-default">
        <div className="panel-heading"><i className="fas fa-gavel"></i> Infraction Info</div>
        <div className="panel-body">
          <InfractionTable infraction={this.props.infraction} />
        </div>
      </div>
    );
  }
}

class GuildInfractionsTable extends Component {
  constructor() {
    super();

    this.state = {
      data: [],
      loading: true,
    };
  }

  render() {
    return (
      <ReactTable
        data={this.state.data.infractions}
        defaultFilterMethod={(filter, row) =>
            String(row[filter.id]) === filter.value}
        columns={[
          {Header: "ID", accessor: "id", width: 50},
          {Header: "User", id: "user", accessor: d => `${d.user.username}#${String(d.user.discriminator).padStart(4, "0")}`, filterable: true, maxWidth: 300},
          {Header: "Actor", id: "actor", accessor: d => `${d.actor.username}#${String(d.actor.discriminator).padStart(4, "0")}`, filterable: true, maxWidth: 300},
          {Header: "Created At", id: "created_at", accessor: d => d.created_at ? new Date(d.created_at).toLocaleString() : d.created_at, filterable: false, width: 200},
          {Header: "Expires At", id: "expires_at", accessor: d => d.expires_at ? new Date(d.expires_at).toLocaleString() : d.expires_at, filterable: false, width: 200},
          {Header: "Type", accessor: d => <Infraction type={d.type.name}/>, id: "type", className: 'text-center allow-overflow', width: 100},
          {Header: "Reason", accessor: "reason", sortable: false},
          {
            Header: "Active",
            id: "active",
            accessor: d => d.active ? <Affirmative /> : <Denial />,
            sortable: false,
            filterable: false,
            className: 'text-center  allow-overflow',
            width: 75
          },
        ]}
        pages={this.state.data.pages || 0}
        loading={this.state.loading}
        manual
        onFetchData={debounce(this.onFetchData.bind(this), 1500)}
        onFilteredChange={filtered => this.setState({ filtered })}
        filterable={true}
        className="-highlight"
        getTdProps={(state, rowInfo, column, instance) => {
          return {
            onClick: () => {
              this.props.onSelectInfraction(rowInfo.original);
            }
          };
        }}
      />
    );
  }

  onFetchData(state, instance) {
    this.setState({loading: true});

    this.props.guild.getInfractions(state.page + 1, state.pageSize, state.sorted, state.filtered).then((data) => {
      this.setState({
        data: data,
        loading: false,
      });
    });
  }
}

export default class GuildInfractions extends Component {
  constructor() {
    super();

    this.state = {
      guild: null,
      infraction: null,
    };
  }

  componentWillMount() {
    globalState.getGuild(this.props.params.gid).then((guild) => {
      globalState.currentGuild = guild;
      this.setState({guild});
    }).catch((err) => {
      console.error('Failed to load guild', this.props.params.gid);
    });
  }

  componentWillUnmount() {
    globalState.currentGuild = null;
  }

  onSelectInfraction(infraction) {
    this.setState({infraction});
  }

  render() {
    if (!this.state.guild) {
      return <h3>Loading...</h3>;
    }

    return (
      <div className="row config-row">
        <div className="col-lg-12">
          <div className="panel panel-default">
            <div className="panel-heading"><i className="fas fa-gavel"></i> Infractions</div>
            <div className="panel-body">
              <GuildInfractionsTable guild={this.state.guild} onSelectInfraction={this.onSelectInfraction.bind(this)} />
            </div>
          </div>
          {this.state.infraction && <GuildInfractionInfo infraction={this.state.infraction} />}
        </div>
      </div>
    );
  }
}
