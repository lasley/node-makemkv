import React, {Component} from 'react';
import PropTypes from 'prop-types';

import {Button, Form, FormGroup, Input, Label, Table,} from 'reactstrap';

import {actionRipTracks,} from '../api.js'

class DiscInfo extends Component {
    constructor(props) {
        super(props);
        this.state = {
            checkAll: false,
            discName: false,
            selectedTracks: this.props.tracks.map((trackInfo) => {
                return trackInfo;
            })
        };
    }

    // Toggle the checkbox on all tracks.
    toggleAllTracks(event) {
        alert('This functionality is currently disabled.');
        // let $target = $(event.target);
        // this.setState({
        //     checkAll: $target.prop('checked'),
        // });
        // this.getTrackCheckboxes(event.target)
        //     .prop('checked', this.state.checkAll);
    }

    toggleTrack(event) {
        let trackId = event.target.name;
        this.state.selectedTracks[trackId].isSelected = event.target.checked;
    }

    // Command the server to rip certain tracks for this disc.
    ripTracks() {
        let trackIds = [];
        this.state.selectedTracks.forEach((selectedTrack, trackId) => {
            if (selectedTrack.isSelected) {
                trackIds.push(trackId);
            }
        });
        actionRipTracks(
            this.state.discName,
            this.props.driveId,
            trackIds
        );
    }

    render(){
        return (<div>
            <h1 className={ this.props.name ? 'invisible' : '' }>
                Drive is {this.props.driveState}
            </h1>
            <Form onSubmit={ this.handleSubmit }
                  className={ !this.props.name ? 'invisible' : '' }
                  >
                <fieldset { ...(this.props.isRipping ? {disabled: 'disabled'} : {}) } >
                    <FormGroup>
                        <Label for="discName">
                            Name
                        </Label>
                        <Input type="text"
                               value={ this.state.discName || this.props.name }
                               onChange={
                                   (event) => {
                                       this.setState({discName: event.target.value})
                                   }
                               }
                               />
                    </FormGroup>
                    <FormGroup name="discInfo">
                        <Table className="discInfo">
                            <thead>
                                <tr>
                                    <th>
                                        <Input type="checkbox"
                                               { ...(this.state.checkAll ? {checked: 'checked'}: {}) }
                                               onChange={ (e) => this.toggleAllTracks(e) } />
                                    </th>
                                    <th>#</th>
                                    <th>Source</th>
                                    <th>Chptrs</th>
                                    <th>Size</th>
                                    <th>Streams</th>
                                    <th>Segments</th>
                                </tr>
                            </thead>
                            <tbody>
                            {this.props.tracks && this.props.tracks.map((trackInfo, trackId) => {
                                return <tr>
                                    <td>
                                        <Input type="checkbox"
                                               name={trackId}
                                               checked={this.state.selectedTracks[trackId].isSelected}
                                               onChange={(event) => this.toggleTrack(event)}
                                            />
                                    </td>
                                    <td>{ trackInfo.orderWeight }</td>
                                    <td>{ trackInfo.name }</td>
                                    <td>{ trackInfo.chapterCount }</td>
                                    <td>{ trackInfo.diskSize }</td>
                                    <td>{ trackInfo.streams.length }</td>
                                    <td>{ trackInfo.segmentsMap }</td>
                                </tr>;
                            })}
                            </tbody>
                        </Table>
                    </FormGroup>
                    <FormGroup>
                        <Button onClick={() => this.ripTracks()}>
                            Rip Tracks
                        </Button>
                    </FormGroup>
                </fieldset>
            </Form>
        </div>);
    }
}

DiscInfo.propTypes = {
    driveState: PropTypes.string.isRequired,
    isRipping: PropTypes.bool,
    metadataLngCode: PropTypes.string.isRequired,
    metadataLngName: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    orderWeight: PropTypes.number.isRequired,
    panelTitle: PropTypes.string,
    sanitized: PropTypes.string,
    treeInfo: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    volumeName: PropTypes.string.isRequired,
    tracks: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.number.isRequired,
        isSelected: PropTypes.bool,
        ripStatus: PropTypes.oneOf(['none', 'busy', 'fail', 'success']),
        chapterCount: PropTypes.number.isRequired,
        diskSize: PropTypes.string.isRequired,
        diskSizeBytes: PropTypes.number.isRequired,
        duration: PropTypes.string.isRequired,
        metadataLngCode: PropTypes.string.isRequired,
        metadataLngName: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        orderWeight: PropTypes.number.isRequired,
        outputFilename: PropTypes.string.isRequired,
        panelTitle: PropTypes.string,
        segmentsCount: PropTypes.number.isRequired,
        segmentsMap: PropTypes.string.isRequired,
        sourceFileName: PropTypes.string.isRequired,
        treeInfo: PropTypes.string.isRequired,
        streams: PropTypes.arrayOf(
            PropTypes.objectOf(PropTypes.string)
        ),
    })),
};

DiscInfo.defaultProps = {
    isRipping: false,
};

export default DiscInfo;
